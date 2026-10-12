"""Ruta docente, paso 1: cursos, diagnóstico y resultado."""
import pytest

from app import db
from app.diagnostico import IDS_ITEMS, PRINCIPIOS, evaluar, faltantes
from app.models import CursoDocente, Usuario
from conftest import token_csrf


def crear_usuario(app, correo, rol):
    with app.app_context():
        u = Usuario(nombre='Otra', apellidos='Persona', correo=correo, rol=rol)
        u.establecer_contrasena('clave-de-prueba-2')
        db.session.add(u)
        db.session.commit()


def entrar(client, correo='docente@demo.example', clave='clave-de-prueba-1'):
    client.post('/login', data={'correo': correo, 'contrasena': clave,
                                'csrf_token': token_csrf(client)})


def nuevo_curso(client, **extra):
    datos = {'nombre': 'Programación estructurada', 'modalidad': 'presencial',
             'csrf_token': token_csrf(client, '/ruta-docente/curso/nuevo')}
    datos.update(extra)
    return client.post('/ruta-docente/curso/nuevo', data=datos)


# ── Instrumento (sin Flask) ──────────────────────────────────────────────
def test_ids_de_items_son_unicos():
    assert len(IDS_ITEMS) == len(set(IDS_ITEMS)) == 14


def test_todo_si_da_100_y_sin_sugerencias():
    r = evaluar({i: 'si' for i in IDS_ITEMS})
    assert all(p['porcentaje'] == 100 for p in r['principios'])
    assert r['sugerencias'] == [] and r['por_explorar'] == []


def test_todo_no_da_cero_y_tres_sugerencias_faciles_primero():
    r = evaluar({i: 'no' for i in IDS_ITEMS})
    assert all(p['porcentaje'] == 0 for p in r['principios'])
    assert len(r['sugerencias']) == 3
    assert all(s['esfuerzo'] == 1 for s in r['sugerencias'])


def test_no_lo_se_cuenta_cero_y_se_lista_por_explorar():
    respuestas = {i: 'si' for i in IDS_ITEMS}
    respuestas['r1'] = 'no_se'
    r = evaluar(respuestas)
    assert [i['id'] for i in r['por_explorar']] == ['r1']
    assert r['sugerencias'][0]['id'] == 'r1'
    assert r['principios'][0]['porcentaje'] < 100


def test_faltantes_detecta_vacios_y_valores_invalidos():
    respuestas = {i: 'si' for i in IDS_ITEMS}
    respuestas['a1'] = 'quizas'
    del respuestas['i2']
    assert set(faltantes(respuestas)) == {'a1', 'i2'}


# ── Rutas ────────────────────────────────────────────────────────────────
def test_requiere_sesion(client):
    r = client.get('/ruta-docente/')
    assert r.status_code == 302 and '/login' in r.headers['Location']


def test_estudiante_no_entra(client, app):
    crear_usuario(app, 'est@demo.example', 'estudiante')
    entrar(client, 'est@demo.example', 'clave-de-prueba-2')
    r = client.get('/ruta-docente/')
    assert r.status_code == 302 and '/login' not in r.headers['Location']


def test_flujo_completo(client, app):
    entrar(client)
    r = nuevo_curso(client, num_estudiantes='30', observaciones='Quiero mejorar mis videos')
    assert r.status_code == 302 and '/diagnostico' in r.headers['Location']
    ruta = r.headers['Location']
    html = client.get(ruta).get_data(as_text=True)
    assert 'Diagnóstico del curso' in html and html.count('<fieldset') == 14

    datos = {i: 'si' for i in IDS_ITEMS}
    datos['r2'] = 'no'
    datos['csrf_token'] = token_csrf(client, ruta)
    r = client.post(ruta, data=datos)
    assert r.status_code == 302 and r.headers['Location'].endswith('/resultado')
    html = client.get(r.headers['Location']).get_data(as_text=True)
    assert 'Para empezar' in html and 'descripción en texto' in html
    with app.app_context():
        assert CursoDocente.query.one().tiene_diagnostico


def test_diagnostico_incompleto_no_se_guarda_y_conserva_respuestas(client, app):
    entrar(client)
    ruta = nuevo_curso(client).headers['Location']
    datos = {'r1': 'si', 'r2': 'parcial', 'csrf_token': token_csrf(client, ruta)}
    r = client.post(ruta, data=datos)
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert 'Falta responder 12' in html
    assert html.count('checked') == 2  # se conservan las dos respuestas dadas
    with app.app_context():
        assert not CursoDocente.query.one().tiene_diagnostico


def test_valor_invalido_se_trata_como_no_respondido(client):
    entrar(client)
    ruta = nuevo_curso(client).headers['Location']
    datos = {i: 'si' for i in IDS_ITEMS}
    datos['a1'] = '<script>'
    datos['csrf_token'] = token_csrf(client, ruta)
    r = client.post(ruta, data=datos)
    assert r.status_code == 200 and 'Falta responder 1 ' in r.get_data(as_text=True)


def test_curso_ajeno_responde_404(client, app):
    crear_usuario(app, 'otro@demo.example', 'docente')
    entrar(client, 'otro@demo.example', 'clave-de-prueba-2')
    ruta = nuevo_curso(client).headers['Location']
    client.get('/salir')
    entrar(client)
    for sufijo in ('/diagnostico', '/resultado'):
        assert client.get(ruta.replace('/diagnostico', sufijo)).status_code == 404
    token = token_csrf(client, '/ruta-docente/curso/nuevo')
    assert client.post(ruta.replace('/diagnostico', '/eliminar'), data={'csrf_token': token}).status_code == 404


def test_resultado_sin_diagnostico_redirige_al_formulario(client):
    entrar(client)
    ruta = nuevo_curso(client).headers['Location']
    r = client.get(ruta.replace('/diagnostico', '/resultado'))
    assert r.status_code == 302 and r.headers['Location'].endswith('/diagnostico')


def test_eliminar_curso(client, app):
    entrar(client)
    ruta = nuevo_curso(client).headers['Location']
    token = token_csrf(client, '/ruta-docente/')
    r = client.post(ruta.replace('/diagnostico', '/eliminar'), data={'csrf_token': token})
    assert r.status_code == 302
    with app.app_context():
        assert CursoDocente.query.count() == 0


def test_eliminar_sin_token_no_borra(client, app):
    entrar(client)
    ruta = nuevo_curso(client).headers['Location']
    client.post(ruta.replace('/diagnostico', '/eliminar'), data={})
    with app.app_context():
        assert CursoDocente.query.count() == 1


def test_nombre_obligatorio_y_html_se_escapa(client):
    entrar(client)
    r = nuevo_curso(client, nombre='')
    assert r.status_code == 200
    nuevo_curso(client, nombre='<img src=x onerror=alert(1)>')
    html = client.get('/ruta-docente/').get_data(as_text=True)
    assert '<img src=x' not in html and '&lt;img' in html
