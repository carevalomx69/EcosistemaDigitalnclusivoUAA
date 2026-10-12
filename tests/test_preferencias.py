from app import db
from app.models import Usuario
from tests.conftest import token_csrf


def iniciar_sesion(client):
    return client.post('/login', data={
        'correo': 'docente@demo.example',
        'contrasena': 'clave-de-prueba-1',
        'csrf_token': token_csrf(client),
    })


def cabecera_csrf(client):
    html = client.get('/').get_data(as_text=True)
    import re
    return {'X-CSRFToken': re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)}


def test_guardar_preferencias_requiere_sesion(client):
    r = client.post('/preferencias', json={'texto': 'grande'})
    assert r.status_code in (302, 400)  # sin sesión (o sin token) no se guarda


def test_guardar_preferencias_exige_token_csrf(app, client):
    iniciar_sesion(client)
    r = client.post('/preferencias', json={'texto': 'grande'})  # sin cabecera X-CSRFToken
    assert r.status_code == 302
    with app.app_context():
        assert Usuario.query.first().pref_tamano_texto == 'normal'


def test_guardar_preferencias_persiste_en_el_perfil(app, client):
    iniciar_sesion(client)
    cab = cabecera_csrf(client)
    r = client.post('/preferencias', json={'texto': 'muy_grande', 'contraste': 'alto'}, headers=cab)
    assert r.status_code == 204
    with app.app_context():
        u = Usuario.query.first()
        assert (u.pref_tamano_texto, u.pref_contraste) == ('muy_grande', 'alto')
    # al cargar otra página el servidor las entrega en los data-attributes del body
    html = client.get('/').get_data(as_text=True)
    assert 'data-pref-texto="muy_grande"' in html
    assert 'data-pref-contraste="alto"' in html


def test_guardar_preferencias_rechaza_valores_invalidos(client):
    iniciar_sesion(client)
    cab = cabecera_csrf(client)
    assert client.post('/preferencias', json={'texto': 'gigante'}, headers=cab).status_code == 400
    assert client.post('/preferencias', json={'contraste': '<script>'}, headers=cab).status_code == 400
    assert client.post('/preferencias', json={}, headers=cab).status_code == 400


def test_nombres_accesibles_de_la_cabecera(client):
    iniciar_sesion(client)
    html = client.get('/').get_data(as_text=True)
    # el logo no usa un aria-label distinto del texto visible
    assert 'class="logo-bloque" aria-label' not in html
    # los botones A+ y A- tienen su texto visible dentro del nombre accesible
    assert 'A+<span class="oculto-visual"> Aumentar tamaño de texto</span>' in html
    assert 'A-<span class="oculto-visual"> Reducir tamaño de texto</span>' in html
