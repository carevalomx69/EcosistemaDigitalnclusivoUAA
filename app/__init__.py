"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Inicialización de la aplicación Flask
"""
import os
from flask import Flask, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect, CSRFError

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def _uri_base_de_datos():
    """Lee DATABASE_URL y corrige el prefijo antiguo 'postgres://' que usan
    algunos proveedores (SQLAlchemy 2 solo acepta 'postgresql://')."""
    uri = os.environ.get('DATABASE_URL', 'sqlite:///ecosistema.db')
    if uri.startswith('postgres://'):
        uri = 'postgresql://' + uri[len('postgres://'):]
    return uri


# Columnas agregadas después de la primera versión. create_all() no modifica tablas
# existentes, así que una base de datos anterior (por ejemplo, el volumen de Docker
# o el disco de Render) las recibe aquí sin perder datos.
COLUMNAS_NUEVAS = {
    'usuarios': [
        ('aviso_aceptado_en', 'TIMESTAMP'),
        ('aviso_version', 'VARCHAR(30)'),
        ('consiente_investigacion', 'BOOLEAN NOT NULL DEFAULT 0'),
    ],
    'cursos_docente': [
        ('diagnostico_inicial_json', 'TEXT'),
        ('cierre_json', 'TEXT'),
        ('cierre_fecha', 'TIMESTAMP'),
    ],
    'unidades_plan': [
        ('adaptacion_json', 'TEXT'),
        ('verificacion_json', 'TEXT'),
    ],
}


def _agregar_columnas_faltantes():
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    for tabla, columnas in COLUMNAS_NUEVAS.items():
        if not inspector.has_table(tabla):
            continue
        existentes = {c['name'] for c in inspector.get_columns(tabla)}
        for nombre, tipo in columnas:
            if nombre not in existentes:
                valor = tipo.replace('DEFAULT 0', 'DEFAULT false') if db.engine.dialect.name == 'postgresql' else tipo
                with db.engine.begin() as conexion:
                    conexion.execute(text(f'ALTER TABLE {tabla} ADD COLUMN {nombre} {valor}'))


def create_app(config=None):
    app = Flask(__name__)

    en_produccion = os.environ.get('APP_ENV') == 'production'

    # SECRET_KEY: en producción es obligatoria. La clave de desarrollo solo se
    # usa fuera de producción para no exigir configuración al ejecutar en local.
    clave = os.environ.get('SECRET_KEY')
    if not clave:
        if en_produccion:
            raise RuntimeError(
                'Falta la variable de entorno SECRET_KEY. '
                'Es obligatoria cuando APP_ENV=production.'
            )
        clave = 'clave-solo-para-desarrollo-local'

    app.config['SECRET_KEY'] = clave
    app.config['SQLALCHEMY_DATABASE_URI'] = _uri_base_de_datos()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = True

    # Cookies de sesión: no accesibles desde JavaScript, no se envían en
    # solicitudes entre sitios y, en producción, solo por HTTPS.
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = en_produccion
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_SECURE'] = en_produccion

    if config:
        app.config.update(config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Inicia sesión para acceder a esa página.'
    login_manager.login_message_category = 'info'
    csrf.init_app(app)  # exige token en todo POST, también en formularios sin FlaskForm

    @app.errorhandler(CSRFError)
    def token_invalido(_error):
        flash('El formulario expiró o no es válido. Inténtalo de nuevo.', 'error')
        return redirect(url_for('main.inicio'))

    @app.after_request
    def cabeceras_de_seguridad(respuesta):
        respuesta.headers.setdefault('X-Content-Type-Options', 'nosniff')
        respuesta.headers.setdefault('X-Frame-Options', 'DENY')
        respuesta.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        if en_produccion:
            respuesta.headers.setdefault(
                'Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        return respuesta

    # Datos del aviso de privacidad (se completan con variables de entorno)
    @app.context_processor
    def datos_del_aviso():
        from app.aviso import contexto_aviso
        return {'aviso': contexto_aviso()}

    # Registrar blueprint
    from app.routes import main
    app.register_blueprint(main)
    from app.ruta_docente import ruta
    app.register_blueprint(ruta)

    # Crear tablas al inicio
    with app.app_context():
        db.create_all()
        _agregar_columnas_faltantes()

    return app
