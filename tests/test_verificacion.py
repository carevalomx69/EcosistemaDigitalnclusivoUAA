"""Ruta docente, paso 4: verificación de los materiales."""
import io
import re
import sqlite3

from docx import Document

from app import create_app, db
from app.adaptacion import COMPROBACIONES_VALIDAS
from app.models import UnidadPlan
from app.verificacion import (ETIQUETA_METODO, MAX_NOTA, METODO_SUGERIDO, avance, detalle, hallazgos, limpiar,
                              metodos_usados, por_verificar)
from test_adaptacion_wcag import unidad
from test_plan_dua import curso_con_diagnostico, entrar, token

ADAPTACION = {'materiales': ['documento', 'video'],
              'estados': {'doc_titulos': 'cumple', 'doc_alt': 'cumple', 'doc_enlaces': 'pendiente',
                          'vid_subtitulos': 'cumple', 'vid_teclado': 'no_aplica'}}


def ruta_unidad(cid, uid):
    return f'/ruta-docente/curso/{cid}/verificacion/unidad/{uid}'


# ── Catálogo (sin Flask) ─────────────────────────────────────────────────
def test_cada_comprobacion_tiene_un_metodo_sugerido_valido():
    assert set(METODO_SUGERIDO) == set().union(*COMPROBACIONES_VALIDAS.values())
    assert set(METODO_SUGERIDO.values()) <= set(ETIQUETA_METODO)


def test_solo_se_verifica_lo_que_se_declaro_cumplido():
    grupos = por_verificar(ADAPTACION)
    assert [(m['id'], [c[0] for c in filas]) for m, filas in grupos] == [
        ('documento', ['doc_titulos', 'doc_alt']), ('video', ['vid_subtitulos'])]
    assert por_verificar({}) == []
    assert por_verificar({'materiales': ['retirado'], 'estados': {}}) == []


def test_limpiar_valida_resultado_metodo_y_nota():
    datos = {'res_doc_titulos': 'confirmado', 'met_doc_titulos': 'teclado',
             'res_doc_alt': 'hallazgo', 'met_doc_alt': '<x>', 'nota_doc_alt': '  ' + 'a' * 400,
             'res_vid_subtitulos': 'quizas',
             'res_doc_enlaces': 'confirmado'}  # pendiente en el paso 3: no se registra
    out = limpiar(ADAPTACION, datos)
    assert out == {'doc_titulos': {'metodo': 'teclado', 'resultado': 'confirmado', 'nota': ''},
                   'doc_alt': {'metodo': METODO_SUGERIDO['doc_alt'], 'resultado': 'hallazgo', 'nota': 'a' * MAX_NOTA}}


def test_avance_hallazgos_y_metodos():
    v = {'doc_titulos': {'metodo': 'verificador', 'resultado': 'confirmado', 'nota': ''},
         'doc_alt': {'metodo': 'lector', 'resultado': 'hallazgo', 'nota': 'Falta en la figura 2'},
         'doc_enlaces': {'metodo': 'revision', 'resultado': 'confirmado', 'nota': ''}}  # ya no está cumplida
    assert avance(ADAPTACION, v) == {'total': 3, 'confirmadas': 1, 'hallazgos': 1, 'sin_verificar': 1}
    assert hallazgos(ADAPTACION, v) == [('1.1.1', 'Contenido no textual',
                                         'Cada imagen informativa tiene texto alternativo; las decorativas se marcan como decorativas.',
                                         'Falta en la figura 2')]
    assert [m for m, _n in metodos_usados([v, {'x': {'metodo': 'lector'}}])][0].startswith('Verificador')
    assert dict(metodos_usados([v, {'x': {'metodo': 'lector'}}]))[ETIQUETA_METODO['lector']] == 2


def test_detalle_marca_lo_no_verificado():
    out = detalle(ADAPTACION, {'doc_titulos': {'metodo': 'verificador', 'resultado': 'confirmado', 'nota': ''}})
    assert out[0][0] == 'Documentos y páginas de texto'
    assert out[0][1][0][2] == 'Se confirma' and out[0][1][1][2] == 'Sin verificar' and out[0][1][1][3] is None


# ── Rutas ────────────────────────────────────────────────────────────────
def test_verificacion_exige_diagnostico(client, app):
    entrar(client)
    from app.models import CursoDocente, Usuario
    with app.app_context():
        c = CursoDocente(docente_id=Usuario.query.one().id, nombre='Sin diagnóstico')
        db.session.add(c)
        db.session.commit()
        cid = c.id
    r = client.get(f'/ruta-docente/curso/{cid}/verificacion')
    assert r.status_code == 302 and r.headers['Location'].endswith('/diagnostico')


def test_unidad_sin_paso_3_remite_al_paso_3(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid)
    html = client.get(f'/ruta-docente/curso/{cid}/verificacion').get_data(as_text=True)
    assert 'Materiales sin revisar en el paso 3' in html and f'/adaptacion/unidad/{uid}' in html
    html = client.get(ruta_unidad(cid, uid)).get_data(as_text=True)
    assert 'No hay comprobaciones marcadas' in html and 'Guardar verificación' not in html


def test_pagina_muestra_solo_lo_cumplido_con_metodo_sugerido(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion=ADAPTACION)
    html = client.get(ruta_unidad(cid, uid)).get_data(as_text=True)
    assert html.count('class="afirmacion"') == 3
    assert 'name="res_doc_enlaces"' not in html and 'name="res_vid_teclado"' not in html
    assert re.search(r'<option value="reproduccion" selected>', html)  # sugerido para subtítulos
    assert 'quedan 1 comprobaciones por adaptar' in html


def test_guardar_y_ver_problemas_en_el_curso(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion=ADAPTACION)
    r = client.post(ruta_unidad(cid, uid), data={
        'res_doc_titulos': 'confirmado', 'met_doc_titulos': 'verificador',
        'res_doc_alt': 'hallazgo', 'met_doc_alt': 'lector', 'nota_doc_alt': 'Falta en la figura 2',
        'csrf_token': token(client)})
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/curso/{cid}/verificacion')
    with app.app_context():
        assert set(db.session.get(UnidadPlan, uid).verificacion) == {'doc_titulos', 'doc_alt'}
    html = client.get(f'/ruta-docente/curso/{cid}/verificacion').get_data(as_text=True)
    assert '2 de 3 verificadas' in html and '1 con problema' in html
    assert 'Falta en la figura 2' in html and 'Prueba con lector de pantalla' in html
    html = client.get(ruta_unidad(cid, uid)).get_data(as_text=True)
    assert re.search(r'name="res_doc_alt" value="hallazgo"\s+checked', html)
    assert 'value="Falta en la figura 2"' in html


def test_nota_se_escapa(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion=ADAPTACION)
    client.post(ruta_unidad(cid, uid), data={'res_doc_alt': 'hallazgo', 'nota_doc_alt': '<script>x</script>',
                                             'csrf_token': token(client)})
    html = client.get(f'/ruta-docente/curso/{cid}/verificacion').get_data(as_text=True)
    assert '<script>x</script>' not in html and '&lt;script&gt;' in html


def test_sin_token_no_guarda(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion=ADAPTACION)
    client.post(ruta_unidad(cid, uid), data={'res_doc_titulos': 'confirmado'})
    with app.app_context():
        assert db.session.get(UnidadPlan, uid).verificacion == {}


def test_unidad_y_curso_ajenos_responden_404(client, app):
    from datetime import datetime
    from app.aviso import VERSION_AVISO
    from app.models import Usuario
    with app.app_context():
        otro = Usuario(aviso_aceptado_en=datetime.utcnow(), aviso_version=VERSION_AVISO,
                       nombre='Otro', apellidos='Docente', correo='otro@demo.example', rol='docente')
        otro.establecer_contrasena('clave-de-prueba-2')
        db.session.add(otro)
        db.session.commit()
    ajeno = curso_con_diagnostico(app, 'otro@demo.example')
    uid = unidad(app, ajeno, adaptacion=ADAPTACION)
    entrar(client)
    tok = token(client)
    assert client.get(f'/ruta-docente/curso/{ajeno}/verificacion').status_code == 404
    assert client.get(ruta_unidad(ajeno, uid)).status_code == 404
    assert client.post(ruta_unidad(ajeno, uid), data={'res_doc_titulos': 'confirmado',
                                                      'csrf_token': tok}).status_code == 404
    propio = curso_con_diagnostico(app)
    assert client.get(ruta_unidad(propio, uid)).status_code == 404


def test_paso_4_aparece_disponible_y_enlazado(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    unidad(app, cid)
    html = client.get('/ruta-docente/').get_data(as_text=True)
    assert 'Por ahora están disponibles los pasos 1 a 4' in html
    assert f'/ruta-docente/curso/{cid}/verificacion' in html
    html = client.get(f'/ruta-docente/curso/{cid}/adaptacion').get_data(as_text=True)
    assert 'Siguiente: Verificación' in html


# ── Descarga ─────────────────────────────────────────────────────────────
def test_plan_descargado_incluye_la_verificacion(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion=ADAPTACION)
    unidad(app, cid, nombre='Unidad sin paso 3')
    client.post(ruta_unidad(cid, uid), data={'res_doc_alt': 'hallazgo', 'met_doc_alt': 'lector',
                                             'nota_doc_alt': 'Falta en la figura 2', 'csrf_token': token(client)})
    md = client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato=md').get_data(as_text=True)
    assert md.count('#### Verificación') == 1
    assert 'Comprobaciones verificadas: 1 de 3 (se confirman: 0; con problema: 1).' in md
    assert ('1.1.1 Contenido no textual: Se encontró un problema (método: Prueba con lector de pantalla '
            '(NVDA, Narrador o VoiceOver)). Nota: Falta en la figura 2') in md
    assert '1.3.1 Información y relaciones: Sin verificar.' in md
    doc = Document(io.BytesIO(client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato=docx').data))
    assert {p.text: p.style.name for p in doc.paragraphs}['Verificación'] == 'Heading 3'


# ── Base de datos anterior ───────────────────────────────────────────────
def test_base_anterior_recibe_la_columna_de_verificacion(tmp_path):
    ruta = tmp_path / 'vieja.db'
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE unidades_plan (id INTEGER PRIMARY KEY, curso_id INTEGER NOT NULL, orden INTEGER,
          nombre VARCHAR(150) NOT NULL, aprendizaje VARCHAR(300), decisiones_json TEXT, notas TEXT,
          adaptacion_json TEXT, actualizado DATETIME);
        INSERT INTO unidades_plan (curso_id, orden, nombre) VALUES (1, 1, 'Unidad vieja');
    """)
    con.commit()
    con.close()
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{ruta}'})
    with app.app_context():
        assert UnidadPlan.query.one().verificacion == {}
