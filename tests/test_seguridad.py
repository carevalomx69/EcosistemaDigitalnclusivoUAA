import pytest

from app import create_app
from tests.conftest import token_csrf


def iniciar_sesion(client, destino='/login'):
    return client.post(destino, data={
        'correo': 'docente@demo.example',
        'contrasena': 'clave-de-prueba-1',
        'csrf_token': token_csrf(client),
    })


def test_login_sin_token_csrf_es_rechazado(client):
    r = client.post('/login', data={
        'correo': 'docente@demo.example', 'contrasena': 'clave-de-prueba-1'})
    assert r.status_code == 302
    assert r.headers['Location'].endswith('/')
    # no inició sesión: una ruta protegida redirige al login
    assert '/login' in client.get('/modulo').headers['Location']


def test_post_de_panel_sin_token_csrf_es_rechazado(app, client):
    from app.models import Grupo
    iniciar_sesion(client)
    r = client.post('/panel/docente/grupo/nuevo',
                    data={'nombre': 'G', 'carrera': 'C'})
    assert r.status_code == 302  # CSRFError -> redirección con aviso
    with app.app_context():
        assert Grupo.query.count() == 0  # el grupo no se creó


@pytest.mark.parametrize('destino', [
    'https://sitio-malicioso.example/robo',
    '//sitio-malicioso.example',
    'http:/sitio-malicioso.example',
    '/\\sitio-malicioso.example',
])
def test_login_no_redirige_a_sitios_externos(client, destino):
    r = iniciar_sesion(client, f'/login?next={destino}')
    assert r.status_code == 302
    assert 'malicioso' not in r.headers['Location']


def test_login_respeta_rutas_internas(client):
    r = iniciar_sesion(client, '/login?next=/modulo')
    assert r.headers['Location'] == '/modulo'


def test_cabeceras_de_seguridad(client):
    r = client.get('/login')
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert r.headers['X-Frame-Options'] == 'DENY'
    assert 'Referrer-Policy' in r.headers


def test_produccion_exige_secret_key(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.delenv('SECRET_KEY', raising=False)
    with pytest.raises(RuntimeError):
        create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})


def test_produccion_con_secret_key_y_cookies_seguras(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'x' * 32)
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    assert app.config['SESSION_COOKIE_SECURE'] is True
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert 'Strict-Transport-Security' in app.test_client().get('/login').headers
