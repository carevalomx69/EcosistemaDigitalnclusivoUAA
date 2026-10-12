"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Inicialización de la aplicación Flask
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config=None):
    app = Flask(__name__)

    # Configuración base — SECRET_KEY y DATABASE_URL se toman de variables de
    # entorno en producción (Render las inyecta); en local usan estos valores
    # por defecto para no requerir configuración adicional.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ecosistema-uaa-2025-cambiar-en-produccion')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ecosistema.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True

    if config:
        app.config.update(config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Inicia sesión para acceder a esa página.'
    login_manager.login_message_category = 'info'

    # Registrar blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Crear tablas al inicio
    with app.app_context():
        db.create_all()

    return app
