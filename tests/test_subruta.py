"""Despliegue detrás de Nginx bajo una subruta (por ejemplo /ecosistema/).

Reglas que estas pruebas protegen (ver CLAUDE.md):
- Ninguna plantilla ni script usa rutas absolutas a la raíz del servidor.
- Con TRUST_PROXY=1 y X-Forwarded-Prefix, los enlaces generados incluyen el prefijo.
- COOKIE_SECURE=0 permite un piloto por HTTP sin romper el inicio de sesión.
"""
import re
from pathlib import Path

import pytest

from app import create_app

RAIZ = Path(__file__).resolve().parent.parent
PREFIJO = {'X-Forwarded-Prefix': '/ecosistema'}


@pytest.fixture()
def app_proxy():
    return create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TRUST_PROXY': True,
    })


def test_plantillas_sin_rutas_absolutas_a_la_raiz():
    patron = re.compile(r'''(?:href|src|action)\s*=\s*["']/(?!/)''')
    culpables = []
    for ruta in (RAIZ / 'app' / 'templates').rglob('*.html'):
        for n, linea in enumerate(ruta.read_text(encoding='utf-8').splitlines(), 1):
            if patron.search(linea):
                culpables.append(f'{ruta.relative_to(RAIZ)}:{n}')
    assert not culpables, f'Rutas absolutas (usa url_for): {culpables}'


def test_scripts_sin_fetch_a_la_raiz():
    patron = re.compile(r'''fetch\(\s*["']/''')
    for ruta in (RAIZ / 'app' / 'static' / 'js').glob('*.js'):
        assert not patron.search(ruta.read_text(encoding='utf-8')), ruta.name


def test_enlaces_incluyen_el_prefijo(app_proxy):
    html = app_proxy.test_client().get('/login', headers=PREFIJO).get_data(as_text=True)
    assert 'href="/ecosistema/static/css/main.css"' in html
    assert 'name="url-preferencias" content="/ecosistema/preferencias"' in html


def test_sin_proxy_confiable_se_ignora_el_prefijo():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    html = app.test_client().get('/login', headers=PREFIJO).get_data(as_text=True)
    assert 'href="/static/css/main.css"' in html
    assert '/ecosistema/' not in html


def test_redireccion_a_login_conserva_el_prefijo(app_proxy):
    r = app_proxy.test_client().get('/modulo', headers=PREFIJO)
    assert r.status_code == 302
    assert '/ecosistema/login' in r.headers['Location']


def test_cookie_secure_configurable_en_produccion(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', 'clave-de-prueba')
    cfg = {'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'}

    con_https = create_app(cfg)
    assert con_https.config['SESSION_COOKIE_SECURE'] is True
    assert 'Strict-Transport-Security' in con_https.test_client().get('/login').headers

    monkeypatch.setenv('COOKIE_SECURE', '0')
    por_http = create_app(cfg)
    assert por_http.config['SESSION_COOKIE_SECURE'] is False
    assert 'Strict-Transport-Security' not in por_http.test_client().get('/login').headers


def test_aviso_pendiente_conserva_el_prefijo_al_volver(app_proxy):
    """Quien inicia sesión sin haber aceptado el aviso es enviado a aceptarlo y,
    después, de vuelta a la página que quería. Ese destino debe incluir el prefijo."""
    from app import db
    from app.models import Usuario
    with app_proxy.app_context():
        u = Usuario(nombre='Admin', apellidos='Prueba', correo='sin-aviso@demo.example', rol='admin')
        u.establecer_contrasena('clave-de-prueba-1')
        db.session.add(u)
        db.session.commit()

    cliente = app_proxy.test_client()
    html = cliente.get('/login', headers=PREFIJO).get_data(as_text=True)
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
    r = cliente.post('/login', headers=PREFIJO, data={
        'csrf_token': token, 'correo': 'sin-aviso@demo.example', 'contrasena': 'clave-de-prueba-1'})
    assert r.status_code == 302

    r = cliente.get('/panel/admin', headers=PREFIJO)
    assert r.status_code == 302
    destino = r.headers['Location']
    assert '/ecosistema/aviso/aceptar' in destino
    assert 'next=/ecosistema/panel/admin' in destino
