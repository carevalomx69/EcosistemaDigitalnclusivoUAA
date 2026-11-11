"""Ruta docente, paso 3: creación o adaptación de materiales con criterios WCAG 2.2."""
import io
import json
import re
import sqlite3

from docx import Document

from app import create_app, db
from app.adaptacion import (COMPROBACIONES_VALIDAS, MATERIALES, SUGERENCIAS_DEL_PLAN, avance, detalle,
                            limpiar, materiales_sugeridos)
from app.models import UnidadPlan
from app.planeacion import OPCIONES_VALIDAS
from test_plan_dua import curso_con_diagnostico, entrar, token

CRITERIO = re.compile(r'^\d\.\d\.\d{1,2}$')


def unidad(app, cid, decisiones=None, adaptacion=None, nombre='Unidad 1'):
    with app.app_context():
        u = UnidadPlan(curso_id=cid, orden=1, nombre=nombre,
                       decisiones_json=json.dumps(decisiones or {}),
                       adaptacion_json=json.dumps(adaptacion) if adaptacion else None)
        db.session.add(u)
        db.session.commit()
        return u.id


# ── Catálogo (sin Flask) ─────────────────────────────────────────────────
def test_catalogo_tiene_ids_unicos_y_criterios_a_o_aa():
    ids = [c[0] for m in MATERIALES for c in m['comprobaciones']]
    assert len(ids) == len(set(ids))
    assert len({m['id'] for m in MATERIALES}) == len(MATERIALES)
    for m in MATERIALES:
        for cid, criterio, nombre, nivel, que, como in m['comprobaciones']:
            assert CRITERIO.match(criterio) and nivel in ('A', 'AA') and nombre and que and como


def test_sugerencias_apuntan_a_opciones_del_plan_y_materiales_reales():
    for (decision, valor), mid in SUGERENCIAS_DEL_PLAN.items():
        assert valor in OPCIONES_VALIDAS[decision] and mid in COMPROBACIONES_VALIDAS


def test_materiales_sugeridos_en_orden_del_catalogo_y_sin_repetir():
    plan = {'rep_formatos': ['video', 'texto', 'ejemplo'], 'acc_acceso': ['probar'], 'acc_claridad': ['rubrica']}
    assert materiales_sugeridos(plan) == ['documento', 'video', 'actividad']
    assert materiales_sugeridos({}) == []


def test_limpiar_descarta_valores_desconocidos_y_comprobaciones_de_otros_materiales():
    sucio = {'vid_subtitulos': 'cumple', 'doc_titulos': 'pendiente', 'aud_control': '<x>', 'inventada': 'cumple'}
    assert limpiar(['video', 'audio', 'otro', 'video'], sucio) == {
        'materiales': ['video', 'audio'], 'estados': {'vid_subtitulos': 'cumple'}}


def test_avance_cuenta_por_estado():
    a = {'materiales': ['audio'], 'estados': {'aud_transcripcion': 'cumple', 'aud_control': 'no_aplica'}}
    assert avance(a) == {'total': 3, 'cumple': 1, 'pendiente': 0, 'no_aplica': 1, 'sin_revisar': 1, 'atendidas': 2}
    assert avance({})['total'] == 0


def test_material_retirado_del_catalogo_se_ignora():
    a = {'materiales': ['retirado', 'audio'], 'estados': {}}
    assert avance(a)['total'] == 3 and [m for m, _ in detalle(a)] == ['Audios y pódcast']


def test_detalle_usa_etiquetas_legibles():
    out = detalle({'materiales': ['audio'], 'estados': {'aud_transcripcion': 'pendiente'}})
    assert out[0][0] == 'Audios y pódcast'
    assert out[0][1][0][0] == '1.2.1' and out[0][1][0][-1] == 'Por adaptar'
    assert out[0][1][1][-1] == 'Sin revisar'


# ── Rutas ────────────────────────────────────────────────────────────────
def test_adaptacion_exige_diagnostico(client, app):
    entrar(client)
    from app.models import CursoDocente, Usuario
    with app.app_context():
        c = CursoDocente(docente_id=Usuario.query.one().id, nombre='Sin diagnóstico')
        db.session.add(c)
        db.session.commit()
        cid = c.id
    r = client.get(f'/ruta-docente/curso/{cid}/adaptacion')
    assert r.status_code == 302 and r.headers['Location'].endswith('/diagnostico')


def test_sin_unidades_invita_a_planear(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    html = client.get(f'/ruta-docente/curso/{cid}/adaptacion').get_data(as_text=True)
    assert 'Todavía no hay unidades' in html and f'/ruta-docente/curso/{cid}/plan' in html


def test_primera_visita_preselecciona_materiales_del_plan(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, {'rep_formatos': ['video']})
    html = client.get(f'/ruta-docente/curso/{cid}/adaptacion/unidad/{uid}').get_data(as_text=True)
    assert re.search(r'value="video"\s+checked', html)
    assert not re.search(r'value="documento"\s+checked', html)
    assert html.count('class="etiqueta-sugerida"') == 1
    assert html.count('<fieldset') == 1 + len(COMPROBACIONES_VALIDAS['video'])
    assert 'Subtítulos (grabado)' in html


def test_guardar_revision_y_ver_avance(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, {'rep_formatos': ['audio']})
    ruta = f'/ruta-docente/curso/{cid}/adaptacion/unidad/{uid}'
    r = client.post(ruta, data={'materiales': 'audio', 'aud_transcripcion': 'pendiente',
                                'aud_control': 'no_aplica', 'aud_teclado': 'cumple', 'csrf_token': token(client)})
    assert r.status_code == 302 and r.headers['Location'].endswith(f'/curso/{cid}/adaptacion')
    with app.app_context():
        assert db.session.get(UnidadPlan, uid).adaptacion == {
            'materiales': ['audio'],
            'estados': {'aud_transcripcion': 'pendiente', 'aud_control': 'no_aplica', 'aud_teclado': 'cumple'}}
    html = client.get(f'/ruta-docente/curso/{cid}/adaptacion').get_data(as_text=True)
    assert '2 de 3 comprobaciones atendidas' in html and '1 por adaptar' in html
    html = client.get(ruta).get_data(as_text=True)
    assert re.search(r'name="aud_transcripcion" value="pendiente"\s+checked', html)


def test_cambiar_materiales_vuelve_a_la_unidad_y_borra_revision_de_los_quitados(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion={'materiales': ['audio'], 'estados': {'aud_control': 'cumple'}})
    ruta = f'/ruta-docente/curso/{cid}/adaptacion/unidad/{uid}'
    r = client.post(ruta, data={'materiales': ['video'], 'aud_control': 'cumple', 'csrf_token': token(client)})
    assert r.status_code == 302 and r.headers['Location'].endswith(ruta)
    with app.app_context():
        assert db.session.get(UnidadPlan, uid).adaptacion == {'materiales': ['video'], 'estados': {}}


def test_unidad_con_material_retirado_no_falla(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion={'materiales': ['retirado', 'video'], 'estados': {}})
    assert client.get(f'/ruta-docente/curso/{cid}/adaptacion').status_code == 200
    assert client.get(f'/ruta-docente/curso/{cid}/adaptacion/unidad/{uid}').status_code == 200


def test_sin_materiales_no_muestra_comprobaciones(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid, adaptacion={'materiales': [], 'estados': {}})
    html = client.get(f'/ruta-docente/curso/{cid}/adaptacion/unidad/{uid}').get_data(as_text=True)
    assert html.count('<fieldset') == 1 and 'Marca al menos un tipo de material' in html


def test_sin_token_no_guarda(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    uid = unidad(app, cid)
    client.post(f'/ruta-docente/curso/{cid}/adaptacion/unidad/{uid}', data={'materiales': 'video'})
    with app.app_context():
        assert db.session.get(UnidadPlan, uid).adaptacion == {}


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
    uid = unidad(app, ajeno)
    entrar(client)
    tok = token(client)
    assert client.get(f'/ruta-docente/curso/{ajeno}/adaptacion').status_code == 404
    assert client.get(f'/ruta-docente/curso/{ajeno}/adaptacion/unidad/{uid}').status_code == 404
    assert client.post(f'/ruta-docente/curso/{ajeno}/adaptacion/unidad/{uid}',
                       data={'materiales': 'video', 'csrf_token': tok}).status_code == 404
    propio = curso_con_diagnostico(app)
    assert client.get(f'/ruta-docente/curso/{propio}/adaptacion/unidad/{uid}').status_code == 404


def test_paso_3_aparece_disponible_y_enlazado(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    unidad(app, cid)
    html = client.get('/ruta-docente/').get_data(as_text=True)
    assert 'Por ahora están disponibles los pasos 1 a 3' in html
    assert f'/ruta-docente/curso/{cid}/adaptacion' in html
    html = client.get(f'/ruta-docente/curso/{cid}/plan').get_data(as_text=True)
    assert 'Siguiente: Creación o adaptación con WCAG 2.2' in html


# ── Descarga ─────────────────────────────────────────────────────────────
def test_plan_descargado_incluye_la_revision(client, app):
    entrar(client)
    cid = curso_con_diagnostico(app)
    unidad(app, cid, adaptacion={'materiales': ['video'], 'estados': {'vid_subtitulos': 'pendiente'}})
    unidad(app, cid, nombre='Unidad sin revisar')
    md = client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato=md').get_data(as_text=True)
    assert md.count('#### Adaptación con WCAG 2.2') == 1 and '##### Videos' in md
    assert '1.2.2 Subtítulos (grabado) (nivel A)' in md and 'Estado: Por adaptar.' in md
    assert 'Comprobaciones atendidas: 0 de 5 (por adaptar: 1; sin revisar: 4).' in md
    doc = Document(io.BytesIO(client.get(f'/ruta-docente/curso/{cid}/plan/descargar?formato=docx').data))
    estilos = {p.text: p.style.name for p in doc.paragraphs}
    assert estilos['Adaptación con WCAG 2.2'] == 'Heading 3' and estilos['Videos'] == 'Heading 4'


# ── Base de datos anterior ───────────────────────────────────────────────
def test_base_anterior_recibe_la_columna_de_adaptacion(tmp_path):
    ruta = tmp_path / 'vieja.db'
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE unidades_plan (id INTEGER PRIMARY KEY, curso_id INTEGER NOT NULL, orden INTEGER,
          nombre VARCHAR(150) NOT NULL, aprendizaje VARCHAR(300), decisiones_json TEXT, notas TEXT, actualizado DATETIME);
        INSERT INTO unidades_plan (curso_id, orden, nombre) VALUES (1, 1, 'Unidad vieja');
    """)
    con.commit()
    con.close()
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{ruta}'})
    with app.app_context():
        assert UnidadPlan.query.one().adaptacion == {}
