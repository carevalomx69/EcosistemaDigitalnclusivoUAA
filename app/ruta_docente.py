"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Ruta docente: recorrido guiado para quien desea iniciar con enseñanza inclusiva.

Pasos de la ruta:
  1. Diagnóstico del curso      (implementado)
  2. Planeación con DUA         (implementado)
  3. Creación o adaptación con criterios WCAG 2.2 (implementado)
  4. Verificación               (implementado)
  5. Cierre y resumen           (próximamente)
"""
import json
from datetime import datetime
from functools import wraps

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.diagnostico import (OPCIONES, PRINCIPIOS, VALORES_VALIDOS, evaluar, faltantes)
from app.forms import FormCurso, FormUnidad, FormVacio
from app.models import CursoDocente, UnidadPlan
from app import adaptacion, plan_export, planeacion, verificacion

ruta = Blueprint('ruta_docente', __name__, url_prefix='/ruta-docente')

PASOS = (
    {'num': 1, 'titulo': 'Diagnóstico del curso', 'disponible': True},
    {'num': 2, 'titulo': 'Planeación con DUA', 'disponible': True},
    {'num': 3, 'titulo': 'Creación o adaptación con WCAG 2.2', 'disponible': True},
    {'num': 4, 'titulo': 'Verificación', 'disponible': True},
    {'num': 5, 'titulo': 'Cierre y resumen', 'disponible': False},
)


def solo_docentes(vista):
    @wraps(vista)
    @login_required
    def envuelta(*args, **kwargs):
        if current_user.rol not in ('docente', 'admin'):
            flash('Esta ruta es para personas con rol docente.', 'error')
            return redirect(url_for('main.inicio'))
        return vista(*args, **kwargs)
    return envuelta


def _curso_propio_o_404(curso_id):
    """Cada persona solo ve sus cursos; si no es suyo, se responde 404."""
    curso = db.session.get(CursoDocente, curso_id)
    if curso is None or curso.docente_id != current_user.id:
        abort(404)
    return curso


@ruta.route('/')
@solo_docentes
def inicio():
    cursos = current_user.cursos.order_by(CursoDocente.creado.desc()).all()
    return render_template('ruta_docente/inicio.html', pasos=PASOS, cursos=cursos)


@ruta.route('/curso/nuevo', methods=['GET', 'POST'])
@solo_docentes
def curso_nuevo():
    form = FormCurso()
    if form.validate_on_submit():
        curso = CursoDocente(
            docente_id=current_user.id,
            nombre=form.nombre.data.strip(),
            programa=(form.programa.data or '').strip() or None,
            modalidad=form.modalidad.data,
            num_estudiantes=form.num_estudiantes.data,
            plataforma=(form.plataforma.data or '').strip() or None,
            observaciones=(form.observaciones.data or '').strip() or None,
        )
        db.session.add(curso)
        db.session.commit()
        flash('Curso guardado. Ahora responde el diagnóstico.', 'success')
        return redirect(url_for('ruta_docente.diagnostico', curso_id=curso.id))
    return render_template('ruta_docente/curso_form.html', form=form)


@ruta.route('/curso/<int:curso_id>/diagnostico', methods=['GET', 'POST'])
@solo_docentes
def diagnostico(curso_id):
    curso = _curso_propio_o_404(curso_id)
    form = FormVacio()
    respuestas = curso.respuestas_diagnostico
    sin_responder = []
    if form.validate_on_submit():
        respuestas = {k: request.form.get(k) for k in
                      [i['id'] for p in PRINCIPIOS for i in p['items']]
                      if request.form.get(k) in VALORES_VALIDOS}
        sin_responder = faltantes(respuestas)
        if not sin_responder:
            curso.diagnostico_json = json.dumps(respuestas)
            curso.diagnostico_fecha = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('ruta_docente.resultado', curso_id=curso.id))
        flash(f'Falta responder {len(sin_responder)} afirmación(es). Están marcadas abajo.', 'error')
    return render_template('ruta_docente/diagnostico.html', curso=curso, form=form,
                           principios=PRINCIPIOS, opciones=OPCIONES, pasos=PASOS,
                           respuestas=respuestas, sin_responder=sin_responder)


@ruta.route('/curso/<int:curso_id>/resultado')
@solo_docentes
def resultado(curso_id):
    curso = _curso_propio_o_404(curso_id)
    if not curso.tiene_diagnostico:
        return redirect(url_for('ruta_docente.diagnostico', curso_id=curso.id))
    return render_template('ruta_docente/resultado.html', curso=curso,
                           r=evaluar(curso.respuestas_diagnostico), pasos=PASOS)


@ruta.route('/curso/<int:curso_id>/eliminar', methods=['POST'])
@solo_docentes
def curso_eliminar(curso_id):
    curso = _curso_propio_o_404(curso_id)
    if not FormVacio().validate_on_submit():
        abort(400)
    db.session.delete(curso)
    db.session.commit()
    flash('Curso eliminado.', 'success')
    return redirect(url_for('ruta_docente.inicio'))


# ── PASO 2: PLANEACIÓN CON DUA ─────────────────────────────────────────────
def _unidad_propia_o_404(curso, unidad_id):
    unidad = db.session.get(UnidadPlan, unidad_id)
    if unidad is None or unidad.curso_id != curso.id:
        abort(404)
    return unidad


def _requiere_diagnostico(curso):
    """El paso 2 parte del diagnóstico. Devuelve una respuesta de redirección si falta."""
    if not curso.tiene_diagnostico:
        flash('Primero responde el diagnóstico del curso (paso 1).', 'info')
        return redirect(url_for('ruta_docente.diagnostico', curso_id=curso.id))
    return None


@ruta.route('/curso/<int:curso_id>/plan')
@solo_docentes
def plan(curso_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    return render_template('ruta_docente/plan.html', curso=curso, pasos=PASOS,
                           form=FormUnidad(), resumen=evaluar(curso.respuestas_diagnostico),
                           decisiones_tomadas=planeacion.decisiones_tomadas,
                           total=planeacion.TOTAL_DECISIONES, maximo=planeacion.MAX_UNIDADES)


@ruta.route('/curso/<int:curso_id>/plan/unidad', methods=['POST'])
@solo_docentes
def unidad_nueva(curso_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    form = FormUnidad()
    if len(curso.unidades) >= planeacion.MAX_UNIDADES:
        flash(f'Un curso admite hasta {planeacion.MAX_UNIDADES} unidades en este prototipo.', 'error')
    elif form.validate_on_submit():
        unidad = UnidadPlan(curso_id=curso.id, orden=len(curso.unidades) + 1,
                            nombre=form.nombre.data.strip(),
                            aprendizaje=(form.aprendizaje.data or '').strip() or None)
        db.session.add(unidad)
        db.session.commit()
        flash('Unidad agregada. Ahora toma tus decisiones de diseño.', 'success')
        return redirect(url_for('ruta_docente.unidad', curso_id=curso.id, unidad_id=unidad.id))
    else:
        flash('Escribe un nombre para la unidad (de 3 a 150 caracteres).', 'error')
    return redirect(url_for('ruta_docente.plan', curso_id=curso.id))


@ruta.route('/curso/<int:curso_id>/plan/unidad/<int:unidad_id>', methods=['GET', 'POST'])
@solo_docentes
def unidad(curso_id, unidad_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    u = _unidad_propia_o_404(curso, unidad_id)
    form = FormUnidad(obj=u)
    elegidas = u.elegidas
    if form.validate_on_submit():
        elegidas = planeacion.limpiar({d['id']: request.form.getlist(d['id'])
                                       for d in planeacion.DECISIONES})
        u.nombre = form.nombre.data.strip()
        u.aprendizaje = (form.aprendizaje.data or '').strip() or None
        u.notas = (form.notas.data or '').strip() or None
        u.decisiones_json = json.dumps(elegidas)
        db.session.commit()
        flash('Unidad guardada.', 'success')
        return redirect(url_for('ruta_docente.plan', curso_id=curso.id))
    return render_template('ruta_docente/unidad.html', curso=curso, unidad=u, form=form,
                           principios=planeacion.PRINCIPIOS_PLAN, elegidas=elegidas,
                           sugeridas=planeacion.sugeridas(curso.respuestas_diagnostico))


@ruta.route('/curso/<int:curso_id>/plan/unidad/<int:unidad_id>/eliminar', methods=['POST'])
@solo_docentes
def unidad_eliminar(curso_id, unidad_id):
    curso = _curso_propio_o_404(curso_id)
    u = _unidad_propia_o_404(curso, unidad_id)
    if not FormVacio().validate_on_submit():
        abort(400)
    db.session.delete(u)
    db.session.flush()
    for n, restante in enumerate(UnidadPlan.query.filter_by(curso_id=curso.id)
                                 .order_by(UnidadPlan.orden).all(), 1):
        restante.orden = n
    db.session.commit()
    flash('Unidad eliminada.', 'success')
    return redirect(url_for('ruta_docente.plan', curso_id=curso.id))


@ruta.route('/curso/<int:curso_id>/plan/descargar')
@solo_docentes
def plan_descargar(curso_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    formato = request.args.get('formato', 'docx')
    if formato == 'docx':
        contenido = plan_export.a_docx(curso)
        tipo = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif formato == 'md':
        contenido = plan_export.a_markdown(curso).encode('utf-8')
        tipo = 'text/markdown; charset=utf-8'
    else:
        abort(400)
    nombre = plan_export.nombre_de_archivo(curso, formato)
    return Response(contenido, mimetype=tipo,
                    headers={'Content-Disposition': f'attachment; filename="{nombre}"'})


# ── PASO 3: CREACIÓN O ADAPTACIÓN CON WCAG 2.2 ─────────────────────────────
@ruta.route('/curso/<int:curso_id>/adaptacion')
@solo_docentes
def adaptacion_curso(curso_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    return render_template('ruta_docente/adaptacion.html', curso=curso, pasos=PASOS,
                           avance=adaptacion.avance, por_id=adaptacion.POR_ID)


@ruta.route('/curso/<int:curso_id>/adaptacion/unidad/<int:unidad_id>', methods=['GET', 'POST'])
@solo_docentes
def adaptacion_unidad(curso_id, unidad_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    u = _unidad_propia_o_404(curso, unidad_id)
    sugeridos = adaptacion.materiales_sugeridos(u.elegidas)
    actual = u.adaptacion or {'materiales': sugeridos, 'estados': {}}
    form = FormVacio()
    if form.validate_on_submit():
        nuevo = adaptacion.limpiar(request.form.getlist('materiales'), request.form)
        cambiaron = nuevo['materiales'] != actual['materiales']
        u.adaptacion_json = json.dumps(nuevo)
        db.session.commit()
        if cambiaron:
            flash('Materiales actualizados. Revisa las comprobaciones de cada uno.', 'success')
            return redirect(url_for('ruta_docente.adaptacion_unidad', curso_id=curso.id, unidad_id=u.id))
        flash('Revisión guardada.', 'success')
        return redirect(url_for('ruta_docente.adaptacion_curso', curso_id=curso.id))
    return render_template('ruta_docente/adaptacion_unidad.html', curso=curso, unidad=u, form=form,
                           pasos=PASOS, materiales=adaptacion.MATERIALES, estados=adaptacion.ESTADOS,
                           actual=actual, sugeridos=sugeridos, avance=adaptacion.avance(actual))


# ── PASO 4: VERIFICACIÓN ───────────────────────────────────────────────────
@ruta.route('/curso/<int:curso_id>/verificacion')
@solo_docentes
def verificacion_curso(curso_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    return render_template('ruta_docente/verificacion.html', curso=curso, pasos=PASOS,
                           avance=verificacion.avance, avance_paso3=adaptacion.avance,
                           hallazgos=verificacion.hallazgos,
                           metodos=verificacion.metodos_usados([u.verificacion for u in curso.unidades]))


@ruta.route('/curso/<int:curso_id>/verificacion/unidad/<int:unidad_id>', methods=['GET', 'POST'])
@solo_docentes
def verificacion_unidad(curso_id, unidad_id):
    curso = _curso_propio_o_404(curso_id)
    falta = _requiere_diagnostico(curso)
    if falta:
        return falta
    u = _unidad_propia_o_404(curso, unidad_id)
    form = FormVacio()
    if form.validate_on_submit():
        u.verificacion_json = json.dumps(verificacion.limpiar(u.adaptacion, request.form))
        db.session.commit()
        flash('Verificación guardada.', 'success')
        return redirect(url_for('ruta_docente.verificacion_curso', curso_id=curso.id))
    return render_template('ruta_docente/verificacion_unidad.html', curso=curso, unidad=u, form=form,
                           pasos=PASOS, grupos=verificacion.por_verificar(u.adaptacion),
                           registros=u.verificacion, metodos=verificacion.METODOS,
                           resultados=verificacion.RESULTADOS, sugerido=verificacion.METODO_SUGERIDO,
                           etiqueta_metodo=verificacion.ETIQUETA_METODO, max_nota=verificacion.MAX_NOTA,
                           avance=verificacion.avance(u.adaptacion, u.verificacion),
                           avance_paso3=adaptacion.avance(u.adaptacion))
