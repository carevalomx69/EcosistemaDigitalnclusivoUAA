"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Formularios Flask-WTF
WCAG 3.3.2: Todos los campos tienen etiquetas y ayuda contextual
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


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
