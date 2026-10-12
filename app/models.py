"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Modelos de base de datos
SQLAlchemy + Flask-Login
"""
from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def cargar_usuario(user_id):
    return Usuario.query.get(int(user_id))


# ── MODELO: USUARIO ────────────────────────────────────────────────────────
class Usuario(UserMixin, db.Model):
    """
    Usuario del ecosistema. Los roles posibles son: estudiante, docente, admin.

    Las preferencias de accesibilidad son el núcleo del perfil inclusivo:
    el sistema se adapta dinámicamente a estas preferencias, sin solicitar
    ni almacenar diagnósticos médicos — decisión ética + DUA (autonomía).
    """
    __tablename__ = 'usuarios'

    id              = db.Column(db.Integer, primary_key=True)
    nombre          = db.Column(db.String(100), nullable=False)
    apellidos       = db.Column(db.String(100), nullable=False)
    correo          = db.Column(db.String(150), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(256), nullable=False)
    rol             = db.Column(db.String(20), default='estudiante')
    carrera         = db.Column(db.String(100))
    activo          = db.Column(db.Boolean, default=True)
    creado          = db.Column(db.DateTime, default=datetime.utcnow)
    grupo_id        = db.Column(db.Integer, db.ForeignKey('grupos.id'), nullable=True)

    # ── Perfil de preferencias de accesibilidad (no diagnóstico médico) ──
    # Microsistema: la interfaz se adapta dinámicamente a estas preferencias
    pref_tamano_texto    = db.Column(db.String(20), default='normal')
    pref_contraste       = db.Column(db.String(20), default='normal')
    pref_velocidad_audio = db.Column(db.Float, default=1.0)
    pref_densidad        = db.Column(db.String(20), default='normal')
    pref_formatos        = db.Column(db.String(100), default='texto')  # CSV: texto,audio,video

    # Relaciones
    respuestas = db.relationship('RespuestaUsuario', backref='usuario', lazy='dynamic')

    # ── Propiedades auxiliares ─────────────────────────────────────────────
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"

    @property
    def nombre_corto(self):
        return self.nombre.split()[0] if self.nombre else ''

    @property
    def formatos_lista(self):
        return self.pref_formatos.split(',') if self.pref_formatos else ['texto']

    def establecer_contrasena(self, contrasena):
        self.contrasena_hash = generate_password_hash(contrasena)

    def verificar_contrasena(self, contrasena):
        return check_password_hash(self.contrasena_hash, contrasena)

    def __repr__(self):
        return f'<Usuario {self.correo} [{self.rol}]>'


# ── MODELO: GRUPO ──────────────────────────────────────────────────────────
class Grupo(db.Model):
    """
    Grupos de estudiantes por carrera o cohorte.
    Mesosistema: articula la plataforma con los contextos académicos específicos.
    """
    __tablename__ = 'grupos'

    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(100), nullable=False)
    carrera    = db.Column(db.String(100), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    creado     = db.Column(db.DateTime, default=datetime.utcnow)
    activo     = db.Column(db.Boolean, default=True)

    # Configuración de accesibilidad del módulo para este grupo (Exosistema)
    config_tiempo_actividad     = db.Column(db.Integer, default=0)   # 0 = sin límite
    config_intentos_actividad   = db.Column(db.Integer, default=0)   # 0 = ilimitados
    config_retroalimentacion    = db.Column(db.String(30), default='inmediata')

    # Relaciones
    estudiantes = db.relationship('Usuario', backref='grupo',
                                  foreign_keys='Usuario.grupo_id', lazy='dynamic')
    docente     = db.relationship('Usuario', foreign_keys=[docente_id])

    @property
    def progreso_promedio(self):
        """Calcula el progreso promedio de todos los estudiantes del grupo."""
        from sqlalchemy import func
        total = self.estudiantes.count()
        if total == 0:
            return 0
        completadas = db.session.query(func.count(RespuestaUsuario.id)).join(Usuario).filter(
            Usuario.grupo_id == self.id
        ).scalar() or 0
        total_actividades = Actividad.query.count() or 1
        return round((completadas / (total * total_actividades)) * 100)

    def __repr__(self):
        return f'<Grupo {self.nombre}>'


# ── MODELO: MÓDULO PEDAGÓGICO ─────────────────────────────────────────────
class Modulo(db.Model):
    """
    Módulo pedagógico con contenido en múltiples formatos.
    DUA: representación múltiple — el mismo contenido en texto, audio, video e infografía.
    """
    __tablename__ = 'modulos'

    id          = db.Column(db.Integer, primary_key=True)
    titulo      = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    activo      = db.Column(db.Boolean, default=True)
    creado      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    secciones  = db.relationship('SeccionModulo', backref='modulo',
                                  order_by='SeccionModulo.orden', lazy='dynamic')
    actividades = db.relationship('Actividad', backref='modulo', lazy='dynamic')

    def __repr__(self):
        return f'<Modulo {self.titulo}>'


class SeccionModulo(db.Model):
    """Sección individual del módulo con contenido multi-formato."""
    __tablename__ = 'secciones_modulo'

    id          = db.Column(db.Integer, primary_key=True)
    modulo_id   = db.Column(db.Integer, db.ForeignKey('modulos.id'), nullable=False)
    orden       = db.Column(db.Integer, default=0)
    titulo      = db.Column(db.String(200), nullable=False)
    icono       = db.Column(db.String(10), default='📄')

    # Contenido en múltiples formatos — DUA: representación
    contenido_texto      = db.Column(db.Text)
    ruta_audio           = db.Column(db.String(300))
    transcripcion_audio  = db.Column(db.Text)
    ruta_video           = db.Column(db.String(300))
    ruta_subtitulos      = db.Column(db.String(300))
    ruta_infografia      = db.Column(db.String(300))
    alt_text_infografia  = db.Column(db.Text)   # WCAG 1.1.1

    @property
    def completada(self):
        """Indica si la sección tiene al menos contenido en texto."""
        return bool(self.contenido_texto)

    def __repr__(self):
        return f'<Seccion {self.titulo}>'


# ── MODELO: ACTIVIDAD ──────────────────────────────────────────────────────
class Actividad(db.Model):
    """
    Actividad de evaluación formativa con tres modos de respuesta.
    DUA: acción y expresión diversa — el estudiante elige cómo responder.
    """
    __tablename__ = 'actividades'

    id        = db.Column(db.Integer, primary_key=True)
    modulo_id = db.Column(db.Integer, db.ForeignKey('modulos.id'), nullable=False)
    titulo    = db.Column(db.String(200), nullable=False)
    pregunta  = db.Column(db.Text, nullable=False)
    tipo      = db.Column(db.String(30), default='seleccion')  # seleccion, texto, visual

    # Opciones para selección múltiple (JSON como string)
    opciones_json      = db.Column(db.Text)
    respuesta_correcta = db.Column(db.String(10))
    retroalimentacion  = db.Column(db.Text)

    # Para selección visual: imágenes con alt text — WCAG 1.1.1
    ruta_imagen_a      = db.Column(db.String(300))
    alt_imagen_a       = db.Column(db.Text)
    ruta_imagen_b      = db.Column(db.String(300))
    alt_imagen_b       = db.Column(db.Text)

    # Relaciones
    respuestas = db.relationship('RespuestaUsuario', backref='actividad', lazy='dynamic')

    @property
    def opciones(self):
        import json
        if self.opciones_json:
            try:
                return json.loads(self.opciones_json)
            except Exception:
                return []
        return []

    def __repr__(self):
        return f'<Actividad {self.titulo}>'


# ── MODELO: RESPUESTA DEL USUARIO ─────────────────────────────────────────
class RespuestaUsuario(db.Model):
    """
    Registro de respuestas y progreso del estudiante.
    Permite el análisis desagregado por condición en la evaluación doctoral.
    """
    __tablename__ = 'respuestas_usuarios'

    id           = db.Column(db.Integer, primary_key=True)
    usuario_id   = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    actividad_id = db.Column(db.Integer, db.ForeignKey('actividades.id'), nullable=False)
    modo_respuesta = db.Column(db.String(20))   # seleccion, texto, visual
    contenido    = db.Column(db.Text)           # La respuesta del usuario
    es_correcta  = db.Column(db.Boolean)
    intento      = db.Column(db.Integer, default=1)
    creado       = db.Column(db.DateTime, default=datetime.utcnow)
    # Preferencias activas en el momento de la sesión (para análisis de evaluación)
    prefs_snapshot = db.Column(db.String(200))

    def __repr__(self):
        return f'<Respuesta usuario={self.usuario_id} actividad={self.actividad_id}>'


# ── MODELO: TÉRMINO DE GLOSARIO ────────────────────────────────────────────
class TerminoGlosario(db.Model):
    """Términos del glosario expandible — WCAG 3.1.3, Mesosistema."""
    __tablename__ = 'glosario'

    id         = db.Column(db.Integer, primary_key=True)
    termino    = db.Column(db.String(100), nullable=False)
    definicion = db.Column(db.Text, nullable=False)
    activo     = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Termino {self.termino}>'
