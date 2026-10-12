"""Progreso por sección del módulo: cada sección se marca de forma independiente."""
import pytest

from app import db
from app.models import Modulo, ProgresoSeccion, SeccionModulo, Usuario
from conftest import token_csrf


@pytest.fixture()
def modulo_con_secciones(app):
    with app.app_context():
        m = Modulo(titulo='Módulo X', activo=True)
        db.session.add(m)
        db.session.flush()
        ids = []
        for n in range(1, 5):
            s = SeccionModulo(modulo_id=m.id, orden=n, titulo=f'Sección {n}',
                              contenido_texto=f'<p>Contenido {n}</p>')
            db.session.add(s)
            db.session.flush()
            ids.append(s.id)
        db.session.commit()
        return ids


def iniciar_sesion(client, correo='docente@demo.example', clave='clave-de-prueba-1'):
    client.post('/login', data={'correo': correo, 'contrasena': clave,
                                'csrf_token': token_csrf(client)})


def test_sin_avance_el_progreso_es_cero(client, modulo_con_secciones):
    iniciar_sesion(client)
    html = client.get('/modulo').get_data(as_text=True)
    assert '0% completado' in html
    assert 'Sección 1 de 4' in html


def test_completar_una_seccion_no_completa_las_demas(client, app, modulo_con_secciones):
    iniciar_sesion(client)
    token = token_csrf(client, '/modulo')
    r = client.post(f'/modulo/seccion/{modulo_con_secciones[0]}/completar', data={'csrf_token': token})
    assert r.status_code == 302
    assert f'seccion={modulo_con_secciones[1]}' in r.headers['Location']
    html = client.get('/modulo').get_data(as_text=True)
    assert '25% completado' in html
    assert '1 de 4 secciones' in html
    with app.app_context():
        assert ProgresoSeccion.query.count() == 1


def test_completar_dos_veces_no_duplica(client, app, modulo_con_secciones):
    iniciar_sesion(client)
    token = token_csrf(client, '/modulo')
    url = f'/modulo/seccion/{modulo_con_secciones[0]}/completar'
    client.post(url, data={'csrf_token': token})
    client.post(url, data={'csrf_token': token})
    with app.app_context():
        assert ProgresoSeccion.query.count() == 1


def test_el_progreso_es_por_persona(client, app, modulo_con_secciones):
    with app.app_context():
        otro = Usuario(nombre='Otra', apellidos='Persona', correo='otra@demo.example', rol='estudiante')
        otro.establecer_contrasena('clave-de-prueba-2')
        db.session.add(otro)
        db.session.commit()
    iniciar_sesion(client)
    client.post(f'/modulo/seccion/{modulo_con_secciones[0]}/completar',
                data={'csrf_token': token_csrf(client, '/modulo')})
    client.get('/salir')
    iniciar_sesion(client, 'otra@demo.example', 'clave-de-prueba-2')
    assert '0% completado' in client.get('/modulo').get_data(as_text=True)


def test_completar_exige_sesion_y_token(client, modulo_con_secciones):
    url = f'/modulo/seccion/{modulo_con_secciones[0]}/completar'
    assert client.post(url).status_code == 302  # sin sesión: redirige a login
    iniciar_sesion(client)
    r = client.post(url, data={})  # con sesión pero sin token CSRF
    assert r.status_code == 302 and '/modulo/seccion' not in r.headers['Location']
    assert 'seccion=' not in r.headers['Location']


def test_seccion_inexistente_responde_404(client, modulo_con_secciones):
    iniciar_sesion(client)
    r = client.post('/modulo/seccion/99999/completar', data={'csrf_token': token_csrf(client, '/modulo')})
    assert r.status_code == 404


def test_menu_enlaza_a_cada_seccion_y_muestra_su_contenido(client, modulo_con_secciones):
    iniciar_sesion(client)
    html = client.get(f'/modulo?seccion={modulo_con_secciones[2]}').get_data(as_text=True)
    assert 'Contenido 3' in html and 'Contenido 1' not in html
    assert 'Sección 3 de 4' in html
    for sid in modulo_con_secciones:
        assert f'/modulo?seccion={sid}' in html
