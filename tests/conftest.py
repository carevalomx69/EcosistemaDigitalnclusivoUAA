import re
import pytest

from app import create_app, db
from app.models import Usuario


@pytest.fixture()
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    })
    with app.app_context():
        db.create_all()
        usuario = Usuario(nombre='Docente', apellidos='Prueba',
                          correo='docente@demo.example', rol='docente')
        usuario.establecer_contrasena('clave-de-prueba-1')
        db.session.add(usuario)
        db.session.commit()
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def token_csrf(client, ruta='/login'):
    html = client.get(ruta).get_data(as_text=True)
    return re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html).group(1)
