"""Ruta docente, paso 5: cierre y resumen."""
import io
import json
import sqlite3

from docx import Document

from app import create_app, db
from app.cierre import MAX_RESPUESTA, comparacion, limpiar, resumen
from app.diagnostico import IDS_ITEMS
from app.models import CursoDocente
from test_adaptacion_wcag import unidad
from test_plan_dua import curso_con_diagnostico, entrar, token
from test_verificacion import ADAPTACION

TODO_SI = {i: 'si' for i in IDS_ITEMS}
TODO_NO = {i: 'no' for i in IDS_ITEMS}
VERIFICADA = {'doc_titulos': {'metodo': 'verificador', 'resultado': 'confirmado', 'nota': ''},
              'doc_alt': {'metodo': 'lector', 'resultado': 'hallazgo', 'nota': 'Falta en la figura 2'}}


def curso(app, cid):
    return db.session.get(CursoDocente, cid)


def unidad_completa(app, cid, nombre='Unidad 1'):
    uid = unidad(app, cid, {'rep_formatos': ['texto']}, adaptacion=ADAPTACION, nombre=nombre)
    with app.app_context():
        from app.models import UnidadPlan
        db.session.get(UnidadPlan, uid).verificacion_json = json.dumps(VERIFICADA)
        db.session.commit()
    return uid


# ── Lógica (sin Flask) ───────────────────────────────────────────────────
def test_comparacion_antes_y_despues():
    assert comparacion({}, TODO_SI) is None
    assert comparacion(TODO_SI, TODO_SI) is None
    out = comparacion(TODO_NO, TODO_SI)
    assert len(out) == 3 and all(c['antes'] == 0 and c['despues'] == 100 and c['cambio'] == 100 for c in out)


def test_limpiar_recorta_y_descarta_campos_desconocidos():
    out = limpiar({'logros': '  Bien  ', 'siguiente': 'x' * 2000, 'otro': 'y'})
    assert out == {'logros': 'Bien', 'dificultades': '', 'siguiente': 'x' * MAX_RESPUESTA}


def test_resumen_suma_los_cuatro_pasos(app):
    cid = curso_con_diagnostico(app)
    unidad_completa(app, cid)
    unidad_completa(app, cid, nombre='Unidad 2')
    with app.app_context():
        r = resumen(curso(app, cid))
    assert r['unidades'] == 2 and r['decisiones'] == {'tomadas': 2, 'total': 16}
    assert r['adaptacion']['total'] == 28 and r['adaptacion']['cumple'] == 6 and r['adaptacion']['pendiente'] == 2
    assert r['verificacion'] == {'total': 6, 'confirmadas': 2, 'hallazgos': 2, 'sin_verificar': 2}
    assert [u for u, _h in r['hallazgos']] == ['Unidad 1', 'Unidad 2']
    assert dict(r['lista'])['Sin problemas pendientes de corregir'] is False
    assert r['completos'] == 5


def test_lista_de_un_curso_recien_diagnosticado(app):
    cid = curso_con_diagnostico(app)
    with app.app_context():
        r = resumen(curso(app, cid))
    assert [hecho for _t, hecho in r['lista']] == [True, False, False, False, False, True]
    assert r['comparacion'] is None and r['verificacion']['total'] == 0


# ── Primer diagnóstico ───────────────────────────────────────────────────
def responder(client, cid, valor):
    return client.post(f'/ruta-docente/curso/{cid}/diagnostico',
                       data={**{i: valor for i in IDS_ITEMS}, 'csrf_token': token(client)})


def test_repetir_el_diagnostico_conserva_el_primero(client, app):
    entrar(client)
    client.post('/ruta-docente/curso/nuevo', data={'nombre': 'Curso nuevo', 'modalidad': 'presencial',
                                                  'csrf_token': token(client)})
    with app.app_context():
        cid = CursoDocente.query.one().id
    responder(client, cid, 'no')
    responder(client, cid, 'parcial')
    responder(client, cid, 'si')
    with app.app_context():
        c = curso(app, cid)
        assert c.respuestas_diagnostico_inicial == TODO_NO and c.respuestas_diagnostico == TODO_SI


def test_curso_anterior_sin_primer_diagnostico_conserva_el_que_tenia(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app, respuestas=TODO_NO)  # creado antes de esta función
    responder(client, cid, 'si')
    with app.app_context():
        assert curso(app, cid).respuestas_diagnostico_inicial == TODO_NO


# ── Rutas ────────────────────────────────────────────────────────────────
def test_cierre_exige_diagnostico(client, app):
    entrar(client)
    from app.models import Usuario
    with app.app_context():
        c = CursoDocente(docente_id=Usuario.query.one().id, nombre='Sin diagnóstico')
        db.session.add(c)
        db.session.commit()
        cid = c.id
    r = client.get(f'/ruta-docente/curso/{cid}/cierre')
    assert r.status_code == 302 and r.headers['Location'].endswith('/diagnostico')


def test_pagina_muestra_resumen_lista_y_pendientes(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    unidad_completa(app, cid)
    html = client.get(f'/ruta-docente/curso/{cid}/cierre').get_data(as_text=True)
    assert '5 de 6 elementos completos' in html
    assert '<span class="cierre-estado">Pendiente</span> Sin problemas pendientes de corregir' in html
    assert '1 unidad(es) · 1 de 8 decisiones tomadas' in html
    assert 'Falta en la figura 2' in html and 'Repetir el diagnóstico' in html
    assert 'Guardar el cierre' in html and 'Ruta completada' not in html


def test_comparacion_aparece_tras_repetir_el_diagnostico(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app, respuestas=TODO_NO)
    responder(client, cid, 'si')
    html = client.get(f'/ruta-docente/curso/{cid}/cierre').get_data(as_text=True)
    assert '<table' in html and '+100 puntos' in html


def test_guardar_cierre(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    r = client.post(f'/ruta-docente/curso/{cid}/cierre', data={
        'logros': 'Subtítulos en todos los videos', 'siguiente': '<b>Rúbricas</b>', 'csrf_token': token(client)})
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/curso/{cid}/cierre')
    with app.app_context():
        c = curso(app, cid)
        assert c.cierre_fecha is not None
        assert c.reflexion == {'logros': 'Subtítulos en todos los videos', 'dificultades': '',
                               'siguiente': '<b>Rúbricas</b>'}
    html = client.get(f'/ruta-docente/curso/{cid}/cierre').get_data(as_text=True)
    assert 'Ruta completada el' in html and 'Actualizar el cierre' in html
    assert '&lt;b&gt;Rúbricas&lt;/b&gt;' in html and '<b>Rúbricas</b>' not in html
    assert 'Ruta completada el' in client.get('/ruta-docente/').get_data(as_text=True)


def test_sin_token_no_cierra(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    client.post(f'/ruta-docente/curso/{cid}/cierre', data={'logros': 'x'})
    with app.app_context():
        assert curso(app, cid).cierre_fecha is None


def test_curso_ajeno_responde_404(client, app):
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
    entrar(client)
    tok = token(client)
    assert client.get(f'/ruta-docente/curso/{ajeno}/cierre').status_code == 404
    assert client.post(f'/ruta-docente/curso/{ajeno}/cierre', data={'logros': 'x', 'csrf_token': tok}).status_code == 404
    with app.app_context():
        assert curso(app, ajeno).cierre_fecha is None


def test_paso_5_enlazado_desde_inicio_y_verificacion(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    unidad(app, cid)
    assert f'/ruta-docente/curso/{cid}/cierre' in client.get('/ruta-docente/').get_data(as_text=True)
    html = client.get(f'/ruta-docente/curso/{cid}/verificacion').get_data(as_text=True)
    assert 'Siguiente: Cierre y resumen' in html and 'ximamente' not in html


# ── Informe descargable ──────────────────────────────────────────────────
def test_informe_incluye_el_cierre_solo_cuando_se_guardo(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app, respuestas=TODO_NO)
    unidad_completa(app, cid)
    responder(client, cid, 'si')
    md = client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato=md').get_data(as_text=True)
    assert '## Cierre y resumen' not in md
    client.post(f'/ruta-docente/curso/{cid}/cierre', data={'logros': 'Subtítulos en todos los videos',
                                                           'csrf_token': token(client)})
    md = client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato=md').get_data(as_text=True)
    assert '## Cierre y resumen' in md and '### Resumen del recorrido' in md
    assert 'Representación: 0 % → 100 % (+100 puntos)' in md
    assert 'Pendiente: Sin problemas pendientes de corregir' in md
    assert 'Unidad 1 · 1.1.1 Contenido no textual' in md and 'Nota: Falta en la figura 2' in md
    assert '**¿Qué funcionó en este recorrido?**' in md and '¿Qué harás en el siguiente ciclo' not in md
    doc = Document(io.BytesIO(client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato=docx').data))
    estilos = {p.text: p.style.name for p in doc.paragraphs}
    assert estilos['Cierre y resumen'] == 'Heading 1' and estilos['Reflexión'] == 'Heading 2'
    assert estilos['¿Qué funcionó en este recorrido?'] == 'Heading 3'
    assert estilos['Subtítulos en todos los videos'] == 'Normal'


def test_informe_sin_reflexion(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    client.post(f'/ruta-docente/curso/{cid}/cierre', data={'csrf_token': token(client)})
    for f in ('docx', 'md'):
        assert client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato={f}').status_code == 200
    assert 'Sin reflexión registrada.' in client.get(
        f'/ruta-docente/curso/{cid}/plan/descargar?formato=md').get_data(as_text=True)


# ── Base de datos anterior ───────────────────────────────────────────────
def test_base_anterior_recibe_las_columnas_del_cierre(tmp_path):
    ruta = tmp_path / 'vieja.db'
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE cursos_docente (id INTEGER PRIMARY KEY, docente_id INTEGER NOT NULL, nombre VARCHAR(150) NOT NULL,
          programa VARCHAR(150), modalidad VARCHAR(20), num_estudiantes INTEGER, plataforma VARCHAR(100),
          observaciones TEXT, creado DATETIME, diagnostico_json TEXT, diagnostico_fecha DATETIME);
        INSERT INTO cursos_docente (docente_id, nombre) VALUES (1, 'Curso viejo');
    """)
    con.commit()
    con.close()
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{ruta}'})
    with app.app_context():
        c = CursoDocente.query.one()
        assert c.cierre_fecha is None and c.reflexion == {} and c.respuestas_diagnostico_inicial == {}
