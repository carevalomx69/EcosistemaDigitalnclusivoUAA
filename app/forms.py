"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Formularios Flask-WTF
WCAG 3.3.2: Todos los campos tienen etiquetas y ayuda contextual
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange


class FormLogin(FlaskForm):
    correo     = StringField('Correo', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired()])
    recordar   = BooleanField('Recordar sesión')


class FormRegistro(FlaskForm):
    nombre             = StringField('Nombre(s)', validators=[DataRequired(), Length(2, 100)])
    apellidos          = StringField('Apellidos', validators=[DataRequired(), Length(2, 100)])
    correo             = StringField('Correo institucional', validators=[DataRequired(), Email()])
    carrera            = SelectField('Carrera', choices=[
        ('', '— Selecciona tu carrera —'),
        ('lic_computacion', 'Licenciatura en Ciencias Computacionales'),
        ('ing_software', 'Ingeniería en Software'),
        ('ing_sistemas', 'Ingeniería en Sistemas Computacionales'),
        ('lic_matematicas', 'Licenciatura en Matemáticas'),
        ('posgrado_computo', 'Maestría/Doctorado en Ciencias Aplicadas de la Computación'),
        ('otra', 'Otra carrera de la UAA'),
    ], validators=[DataRequired()])
    contrasena         = PasswordField('Contraseña', validators=[DataRequired(), Length(8)])
    confirmar_contrasena = PasswordField('Confirmar contraseña',
                            validators=[DataRequired(), EqualTo('contrasena',
                            message='Las contraseñas no coinciden.')])


class FormPerfil(FlaskForm):
    pass  # Los campos se procesan directamente de request.form por ser radios/checkboxes


class FormGrupo(FlaskForm):
    nombre  = StringField('Nombre del grupo', validators=[DataRequired(), Length(3, 100)])
    carrera = SelectField('Carrera', choices=[
        ('', '— Selecciona —'),
        ('lic_computacion', 'Licenciatura en Ciencias Computacionales'),
        ('ing_software', 'Ingeniería en Software'),
        ('ing_sistemas', 'Ingeniería en Sistemas Computacionales'),
        ('posgrado', 'Maestría / Doctorado'),
        ('otra', 'Otra'),
    ], validators=[DataRequired()])


class FormUsuarioAdmin(FlaskForm):
    nombre     = StringField('Nombre(s)', validators=[DataRequired()])
    apellidos  = StringField('Apellidos', validators=[DataRequired()])
    correo     = StringField('Correo', validators=[DataRequired(), Email()])
    rol        = SelectField('Rol', choices=[
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente'),
        ('admin', 'Administrador'),
    ])
    contrasena = PasswordField('Contraseña temporal', validators=[DataRequired(), Length(6)])


class FormActividad(FlaskForm):
    pass  # Los campos se procesan directamente de request.form


class FormCurso(FlaskForm):
    """Datos de contexto del curso (ruta docente, paso 1). Sin datos de estudiantes."""
    nombre = StringField('Nombre del curso', validators=[DataRequired(), Length(3, 150)])
    programa = StringField('Programa educativo', validators=[Optional(), Length(max=150)])
    modalidad = SelectField('Modalidad', choices=[
        ('presencial', 'Presencial'),
        ('hibrida', 'Híbrida'),
        ('en_linea', 'En línea'),
    ], validators=[DataRequired()])
    num_estudiantes = IntegerField('Número aproximado de estudiantes',
                                   validators=[Optional(), NumberRange(1, 500)])
    plataforma = StringField('Plataforma o herramientas que usas', validators=[Optional(), Length(max=100)])
    observaciones = TextAreaField('Qué te gustaría mejorar (opcional)',
                                  validators=[Optional(), Length(max=1000)])


class FormVacio(FlaskForm):
    """Formulario sin campos, solo para validar el token CSRF."""
    pass
