"""Auditoría automática con axe-core y prueba de reflujo a 320 px.

Requiere Playwright y un navegador Chromium:
    pip install -r requirements-dev.txt
    python -m playwright install chromium
Si Chromium está en otra ruta, indícala con la variable CHROMIUM_PATH.
Sin Playwright instalado, estas pruebas se omiten.

Nota: axe detecta solo una parte de los problemas de accesibilidad. Estas pruebas
no sustituyen la revisión manual ni las pruebas con personas usuarias.
"""
import os
import threading
from pathlib import Path

import pytest

sync_api = pytest.importorskip('playwright.sync_api')
from werkzeug.serving import make_server  # noqa: E402

from app import create_app, db  # noqa: E402
from app.models import Usuario  # noqa: E402

AXE = (Path(__file__).parent / 'vendor' / 'axe.min.js').read_text(encoding='utf-8')
ETIQUETAS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice']
PUBLICAS = ['/login', '/registro', '/accesibilidad']
PRIVADAS = ['/', '/modulo', '/panel/docente', '/perfil', '/actividad/1']


@pytest.fixture(scope='module')
def servidor(tmp_path_factory):
    bd = tmp_path_factory.mktemp('bd') / 'axe.db'
    app = create_app({'SQLALCHEMY_DATABASE_URI': f'sqlite:///{bd}', 'TESTING': True})
    with app.app_context():
        u = Usuario(nombre='Docente', apellidos='Prueba',
                    correo='docente@demo.example', rol='docente')
        u.establecer_contrasena('clave-de-prueba-1')
        db.session.add(u)
        db.session.commit()
    srv = make_server('127.0.0.1', 0, app, threaded=True)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    yield f'http://127.0.0.1:{srv.server_port}'
    srv.shutdown()


@pytest.fixture(scope='module')
def navegador():
    with sync_api.sync_playwright() as p:
        opciones = {}
        if os.environ.get('CHROMIUM_PATH'):
            opciones['executable_path'] = os.environ['CHROMIUM_PATH']
            opciones['args'] = ['--no-sandbox']
        try:
            nav = p.chromium.launch(**opciones)
        except Exception as e:  # navegador no instalado
            pytest.skip(f'No se pudo abrir Chromium: {str(e)[:120]}')
        yield nav
        nav.close()


def abrir_sesion(navegador, servidor, ancho=1280):
    ctx = navegador.new_context(viewport={'width': ancho, 'height': 900})
    pagina = ctx.new_page()
    pagina.goto(servidor + '/login')
    pagina.fill('input[name=correo]', 'docente@demo.example')
    pagina.fill('input[name=contrasena]', 'clave-de-prueba-1')
    with pagina.expect_navigation():
        pagina.click('button[type=submit], input[type=submit]')
    return pagina


def violaciones_axe(pagina):
    pagina.add_script_tag(content=AXE)
    return pagina.evaluate(
        """async (tags) => (await axe.run(document, {runOnly: {type: 'tag', values: tags}}))
            .violations.map(v => v.id + ' x' + v.nodes.length + ': ' + v.nodes[0].html.slice(0, 100))""",
        ETIQUETAS)


@pytest.mark.parametrize('ruta', PUBLICAS)
def test_axe_sin_violaciones_en_paginas_publicas(navegador, servidor, ruta):
    pagina = navegador.new_page()
    pagina.goto(servidor + ruta)
    assert violaciones_axe(pagina) == []


@pytest.mark.parametrize('ruta', PRIVADAS)
def test_axe_sin_violaciones_en_paginas_con_sesion(navegador, servidor, ruta):
    pagina = abrir_sesion(navegador, servidor)
    pagina.goto(servidor + ruta)
    assert violaciones_axe(pagina) == []


@pytest.mark.parametrize('ruta', PUBLICAS[:2] + PRIVADAS)
def test_sin_desplazamiento_horizontal_a_320px(navegador, servidor, ruta):
    """WCAG 1.4.10 (reflujo): sin desplazamiento horizontal de la página a 320 px."""
    pagina = abrir_sesion(navegador, servidor, ancho=320)
    pagina.goto(servidor + ruta)
    ancho = pagina.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
    assert ancho[0] <= ancho[1]


def test_navegacion_visible_en_movil(navegador, servidor):
    """La navegación y los controles de accesibilidad no desaparecen en pantallas pequeñas."""
    pagina = abrir_sesion(navegador, servidor, ancho=320)
    assert pagina.is_visible('nav.nav-principal')
    assert pagina.is_visible('#btn-contraste')


def test_ajuste_de_texto_se_conserva_al_navegar(navegador, servidor):
    pagina = abrir_sesion(navegador, servidor)
    pagina.goto(servidor + '/modulo')
    with pagina.expect_response('**/preferencias'):
        pagina.click('button:has-text("A+")')
    pagina.goto(servidor + '/')
    assert 'texto-grande' in pagina.evaluate('document.body.className')
