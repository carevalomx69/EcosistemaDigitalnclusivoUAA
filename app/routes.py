"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Rutas y controladores Flask
"""
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Usuario, Grupo, Modulo, SeccionModulo, Actividad, RespuestaUsuario, TerminoGlosario
from app.forms import FormLogin, FormRegistro, FormPerfil, FormGrupo, FormUsuarioAdmin

main = Blueprint('main', __name__)

ROLES_VALIDOS = ('estudiante', 'docente', 'admin')


def _destino_seguro(destino):
    """Acepta solo rutas internas ('/algo'). Rechaza URLs absolutas o que
    empiezan con '//' para evitar redirecciones a sitios externos."""
    if not destino:
        return None
    partes = urlparse(destino)
    if partes.scheme or partes.netloc or not destino.startswith('/') or destino.startswith('//') or '\\' in destino:
        return None
    return destino


# ── INICIO ─────────────────────────────────────────────────────────────────
@main.route('/')
def inicio():
    return render_template('inicio.html')


# ── AUTENTICACIÓN — WCAG 3.3.7: Sin CAPTCHA ───────────────────────────────
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))
    form = FormLogin()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(correo=form.correo.data.lower().strip()).first()
        if usuario and usuario.verificar_contrasena(form.contrasena.data):
            login_user(usuario, remember=form.recordar.data)
            siguiente = _destino_seguro(request.args.get('next'))
            flash(f'Bienvenido/a, {usuario.nombre_corto}.', 'success')
            return redirect(siguiente or url_for('main.inicio'))
        flash('Correo o contraseña incorrectos. Intenta de nuevo.', 'error')
    return render_template('login.html', form=form)


@main.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.inicio'))
    form = FormRegistro()
    if form.validate_on_submit():
        if Usuario.query.filter_by(correo=form.correo.data.lower().strip()).first():
            flash('Ya existe una cuenta con ese correo.', 'error')
            return render_template('registro.html', form=form)

        # Recoger formatos preferidos del formulario
        formatos = request.form.getlist('pref_formatos')
        formatos_str = ','.join(formatos) if formatos else 'texto'

        usuario = Usuario(
            nombre          = form.nombre.data.strip(),
            apellidos       = form.apellidos.data.strip(),
            correo          = form.correo.data.lower().strip(),
            carrera         = form.carrera.data,
            rol             = 'estudiante',
            # Preferencias de accesibilidad del perfil inicial
            pref_tamano_texto    = request.form.get('pref_tamano_texto', 'normal'),
            pref_contraste       = request.form.get('pref_contraste', 'normal'),
            pref_velocidad_audio = float(request.form.get('pref_velocidad_audio', 1.0)),
            pref_densidad        = request.form.get('pref_densidad', 'normal'),
            pref_formatos        = formatos_str,
        )
        usuario.establecer_contrasena(form.contrasena.data)
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        flash('Cuenta creada correctamente. ¡Bienvenido/a al ecosistema!', 'success')
        return redirect(url_for('main.inicio'))
    return render_template('registro.html', form=form)


@main.route('/salir')
@login_required
def cerrar_sesion():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('main.login'))


# ── MÓDULO PEDAGÓGICO ──────────────────────────────────────────────────────
@main.route('/modulo')
@login_required
def modulo():
    modulo_activo = Modulo.query.filter_by(activo=True).first()
    secciones = []
    if modulo_activo:
        secciones_db = modulo_activo.secciones.all()
        for s in secciones_db:
            completada = RespuestaUsuario.query.filter(
                RespuestaUsuario.usuario_id == current_user.id
            ).join(Actividad).filter(Actividad.modulo_id == modulo_activo.id).first() is not None
            secciones.append({
                'id': s.id, 'titulo': s.titulo,
                'icono': s.icono, 'activa': False, 'completada': completada
            })
        if secciones:
            secciones[0]['activa'] = True
    else:
        # Datos placeholder para la primera versión
        secciones = [
            {'id': 1, 'titulo': 'Introducción al módulo', 'icono': '📖', 'activa': True, 'completada': False},
            {'id': 2, 'titulo': 'Los tres pilares del ecosistema', 'icono': '🏛️', 'activa': False, 'completada': False},
            {'id': 3, 'titulo': 'DUA: Diseño Universal para el Aprendizaje', 'icono': '🎓', 'activa': False, 'completada': False},
            {'id': 4, 'titulo': 'WCAG 2.2 en la práctica', 'icono': '♿', 'activa': False, 'completada': False},
            {'id': 5, 'titulo': 'Perspectiva ecológica', 'icono': '🌐', 'activa': False, 'completada': False},
            {'id': 6, 'titulo': 'Actividades de evaluación', 'icono': '✏️', 'activa': False, 'completada': False},
        ]

    # Glosario del módulo
    glosario = TerminoGlosario.query.filter_by(activo=True).all()
    if not glosario:
        # Términos placeholder
        class _T:
            pass
        terminos_placeholder = [
            ('DUA', 'Diseño Universal para el Aprendizaje (v3.0, CAST 2024). Marco pedagógico que propone diseñar entornos educativos anticipando la diversidad de los aprendices desde el origen.'),
            ('WCAG', 'Web Content Accessibility Guidelines. Pautas del W3C para el diseño accesible de contenidos web. La versión 2.2 (2023) es el estándar actual con criterios de éxito en tres niveles: A, AA y AAA.'),
            ('POUR', 'Acrónimo de los cuatro principios de WCAG: Perceptible, Operable, Comprensible y Robusto.'),
            ('Ecosistema digital', 'Conjunto articulado de actores, tecnologías, prácticas pedagógicas e institucionales que configuran la experiencia educativa digital de manera interdependiente.'),
            ('Microsistema', 'En el modelo de Bronfenbrenner, el entorno inmediato de interacción: plataforma digital, aula virtual, relación docente-estudiante.'),
        ]
        glosario = []
        for termino, definicion in terminos_placeholder:
            t = _T()
            t.termino = termino
            t.definicion = definicion
            glosario.append(t)

    # Calcular progreso
    if modulo_activo:
        total_act = modulo_activo.actividades.count()
        completadas = RespuestaUsuario.query.filter_by(usuario_id=current_user.id).count()
        progreso = round((completadas / total_act) * 100) if total_act > 0 else 0
    else:
        progreso = 0

    seccion_actual = None
    if modulo_activo:
        secciones_db = modulo_activo.secciones.all()
        if secciones_db:
            seccion_actual = secciones_db[0]
    elif secciones:
        class _Sec:
            pass
        seccion_actual = _Sec()
        seccion_actual.titulo = secciones[0]['titulo']
        seccion_actual.contenido_texto = '<p>Un <strong>Ecosistema Digital Educativo Inclusivo</strong> es un conjunto articulado de actores, tecnologías y prácticas pedagógicas...</p>'

    return render_template('modulo.html',
        modulo=modulo_activo,
        secciones=secciones,
        seccion_actual=seccion_actual,
        glosario=glosario,
        progreso=progreso
    )


@main.route('/actividad/<int:id>', methods=['GET', 'POST'])
@login_required
def actividad(id):
    from app.forms import FormActividad
    form = FormActividad()
    actividad_db = Actividad.query.get(id)

    retroalimentacion = None
    correcto = False

    if request.method == 'POST':
        modo = request.form.get('modo_respuesta', 'seleccion')
        if modo == 'seleccion':
            respuesta = request.form.get('respuesta_seleccion', '')
        elif modo == 'texto':
            respuesta = request.form.get('respuesta_texto', '')
        else:
            respuesta = request.form.get('respuesta_visual', '')

        if actividad_db:
            correcto = (respuesta == actividad_db.respuesta_correcta)
            retroalimentacion = actividad_db.retroalimentacion or (
                '¡Correcto! Has completado esta actividad.' if correcto
                else 'Intenta de nuevo. Revisa el contenido del módulo.'
            )
            # Guardar respuesta
            prefs = f"texto={current_user.pref_tamano_texto},contraste={current_user.pref_contraste}"
            resp = RespuestaUsuario(
                usuario_id=current_user.id, actividad_id=id,
                modo_respuesta=modo, contenido=respuesta,
                es_correcta=correcto, prefs_snapshot=prefs
            )
            db.session.add(resp)
            db.session.commit()

    # Datos placeholder si no hay actividad en BD
    if not actividad_db:
        class _A:
            pass
        actividad_db = _A()
        actividad_db.id = id
        actividad_db.titulo = 'Actividad 1: Los principios POUR'
        actividad_db.pregunta = '¿Cuál de los siguientes enunciados describe correctamente los cuatro principios POUR de WCAG 2.2?'
        actividad_db.opciones = [
            {'id': 'a', 'texto': 'Perceptible, Operable, Comprensible, Robusto'},
            {'id': 'b', 'texto': 'Perceptible, Observable, Comprensible, Robusto'},
            {'id': 'c', 'texto': 'Presentable, Operable, Comprensible, Robusto'},
            {'id': 'd', 'texto': 'Perceptible, Operable, Claro, Robusto'},
        ]

    return render_template('actividad.html',
        form=form,
        actividad=actividad_db,
        retroalimentacion=retroalimentacion,
        correcto=correcto
    )


# ── PERFIL DE PREFERENCIAS ─────────────────────────────────────────────────
@main.route('/perfil', methods=['GET', 'POST'])
@login_required
def mi_perfil():
    form = FormPerfil()
    if form.validate_on_submit():
        current_user.pref_tamano_texto    = request.form.get('pref_tamano_texto', 'normal')
        current_user.pref_contraste       = request.form.get('pref_contraste', 'normal')
        current_user.pref_velocidad_audio = float(request.form.get('pref_velocidad_audio', 1.0))
        current_user.pref_densidad        = request.form.get('pref_densidad', 'normal')
        db.session.commit()
        flash('Preferencias guardadas correctamente.', 'success')
        return redirect(url_for('main.mi_perfil'))
    return render_template('perfil.html', form=form)


# ── PANEL DOCENTE ──────────────────────────────────────────────────────────
@main.route('/panel/docente')
@login_required
def panel_docente():
    if current_user.rol not in ['docente', 'admin']:
        flash('No tienes acceso a esa sección.', 'error')
        return redirect(url_for('main.inicio'))
    grupos = Grupo.query.filter_by(docente_id=current_user.id).all()
    total_est = sum(g.estudiantes.count() for g in grupos)
    prom = round(sum(g.progreso_promedio for g in grupos) / len(grupos)) if grupos else 0
    total_resp = RespuestaUsuario.query.join(Usuario).filter(
        Usuario.grupo_id.in_([g.id for g in grupos])
    ).count() if grupos else 0
    form = FormGrupo()
    return render_template('panel_docente.html',
        grupos=grupos,
        total_estudiantes=total_est,
        promedio_progreso=prom,
        actividades_completadas=total_resp,
        form=form
    )


@main.route('/panel/docente/grupo/nuevo', methods=['POST'])
@login_required
def crear_grupo():
    if current_user.rol not in ['docente', 'admin']:
        return redirect(url_for('main.inicio'))
    nombre  = request.form.get('nombre', '').strip()
    carrera = request.form.get('carrera', '').strip()
    if nombre and carrera:
        grupo = Grupo(nombre=nombre, carrera=carrera, docente_id=current_user.id)
        db.session.add(grupo)
        db.session.commit()
        flash(f'Grupo "{nombre}" creado correctamente.', 'success')
    else:
        flash('El nombre y la carrera son obligatorios.', 'error')
    return redirect(url_for('main.panel_docente'))


# ── PANEL ADMIN ────────────────────────────────────────────────────────────
@main.route('/panel/admin')
@login_required
def panel_admin():
    if current_user.rol != 'admin':
        flash('No tienes acceso a esa sección.', 'error')
        return redirect(url_for('main.inicio'))
    usuarios = Usuario.query.order_by(Usuario.creado.desc()).limit(50).all()
    grupos   = Grupo.query.all()
    form     = FormUsuarioAdmin()
    return render_template('panel_admin.html',
        usuarios=usuarios,
        grupos=grupos,
        total_usuarios=Usuario.query.count(),
        total_grupos=Grupo.query.count(),
        total_docentes=Usuario.query.filter_by(rol='docente').count(),
        total_estudiantes=Usuario.query.filter_by(rol='estudiante').count(),
        form=form
    )


@main.route('/panel/admin/usuario/nuevo', methods=['POST'])
@login_required
def crear_usuario_admin():
    if current_user.rol != 'admin':
        return redirect(url_for('main.inicio'))
    nombre     = request.form.get('nombre', '').strip()
    apellidos  = request.form.get('apellidos', '').strip()
    correo     = request.form.get('correo', '').lower().strip()
    rol        = request.form.get('rol', 'estudiante')
    if rol not in ROLES_VALIDOS:
        rol = 'estudiante'
    grupo_id   = request.form.get('grupo_id') or None
    if grupo_id is not None:
        grupo_id = int(grupo_id) if grupo_id.isdigit() else None
    contrasena = request.form.get('contrasena', '')

    if not all([nombre, apellidos, correo, contrasena]):
        flash('Todos los campos obligatorios deben estar completos.', 'error')
        return redirect(url_for('main.panel_admin'))

    if Usuario.query.filter_by(correo=correo).first():
        flash('Ya existe un usuario con ese correo.', 'error')
        return redirect(url_for('main.panel_admin'))

    usuario = Usuario(nombre=nombre, apellidos=apellidos, correo=correo,
                      rol=rol, grupo_id=grupo_id)
    usuario.establecer_contrasena(contrasena)
    db.session.add(usuario)
    db.session.commit()
    flash(f'Usuario {nombre} {apellidos} creado correctamente.', 'success')
    return redirect(url_for('main.panel_admin'))


# ── DECLARACIÓN DE ACCESIBILIDAD ───────────────────────────────────────────
@main.route('/accesibilidad')
def accesibilidad():
    return render_template('accesibilidad.html')
