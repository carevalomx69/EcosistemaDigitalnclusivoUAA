"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Exportación del plan DUA de un curso a Word (.docx) y Markdown.

El documento Word se genera con estilos de título y listas reales, idioma
declarado y título en las propiedades, para que el propio plan sea accesible.
No depende de Flask.
"""
import io
import re
from datetime import datetime

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from app import adaptacion, cierre, verificacion
from app.diagnostico import evaluar
from app.planeacion import etiquetas_elegidas, decisiones_tomadas, TOTAL_DECISIONES

AVISO = ('Documento generado con el prototipo Ecosistema Digital Educativo Inclusivo (UAA). '
         'El diagnóstico es una autoevaluación orientativa y las decisiones son un borrador de trabajo.')
MODALIDADES = {'presencial': 'Presencial', 'hibrida': 'Híbrida', 'en_linea': 'En línea'}


def nombre_de_archivo(curso, extension):
    """Nombre seguro y en ASCII para la descarga."""
    base = re.sub(r'[^a-z0-9]+', '-', _sin_acentos(curso.nombre.lower())).strip('-') or 'curso'
    return f'plan-dua-{base[:40]}.{extension}'


def _sin_acentos(texto):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


def construir(curso):
    """Datos neutrales del plan, usados por los dos formatos."""
    resultado = evaluar(curso.respuestas_diagnostico) if curso.tiene_diagnostico else None
    unidades = []
    for u in curso.unidades:
        unidades.append({
            'nombre': u.nombre,
            'aprendizaje': u.aprendizaje,
            'notas': u.notas,
            'tomadas': decisiones_tomadas(u.elegidas),
            'principios': etiquetas_elegidas(u.elegidas),
            'adaptacion': adaptacion.detalle(u.adaptacion) if u.adaptacion else None,
            'avance': adaptacion.avance(u.adaptacion) if u.adaptacion else None,
            'verificacion': verificacion.detalle(u.adaptacion, u.verificacion),
            'avance_verificacion': verificacion.avance(u.adaptacion, u.verificacion),
        })
    contexto = [('Programa educativo', curso.programa),
                ('Modalidad', MODALIDADES.get(curso.modalidad, curso.modalidad)),
                ('Plataforma o herramientas', curso.plataforma),
                ('Número aproximado de estudiantes', curso.num_estudiantes)]
    return {
        'titulo': f'Plan de inclusión con DUA: {curso.nombre}',
        'fecha': datetime.now().strftime('%d/%m/%Y'),
        'contexto': [(k, str(v)) for k, v in contexto if v],
        'observaciones': curso.observaciones,
        'resultado': resultado,
        'unidades': unidades,
        'cierre': _cierre(curso),
    }


def _cierre(curso):
    """Sección de cierre (paso 5): solo si la persona docente ya guardó el cierre."""
    if not curso.cierre_fecha:
        return None
    r = cierre.resumen(curso)
    a, v = r['adaptacion'], r['verificacion']
    recorrido = [
        'Diagnóstico: ' + '; '.join(f"{p['nombre']} {p['porcentaje']} %" for p in r['diagnostico']['principios']) + '.',
        f"Planeación con DUA: {r['unidades']} unidad(es) y {r['decisiones']['tomadas']} de "
        f"{r['decisiones']['total']} decisiones tomadas.",
        f"Adaptación con WCAG 2.2: {a['atendidas']} de {a['total']} comprobaciones atendidas "
        f"({a['pendiente']} por adaptar y {a['sin_revisar']} sin revisar).",
        f"Verificación: {v['confirmadas'] + v['hallazgos']} de {v['total']} comprobaciones verificadas "
        f"({v['confirmadas']} se confirman y {v['hallazgos']} con problema).",
    ]
    comparacion = [f"{c['nombre']}: {c['antes']} % → {c['despues']} % ({c['cambio']:+d} puntos)"
                   for c in r['comparacion'] or []]
    pendientes = [f'{unidad} · {criterio} {nombre}: {que}' + (f' Nota: {nota}' if nota else '')
                  for unidad, (criterio, nombre, que, nota) in r['hallazgos']]
    reflexion = curso.reflexion
    return {
        'fecha': curso.cierre_fecha.strftime('%d/%m/%Y'),
        'recorrido': recorrido,
        'lista': [f"{'Hecho' if hecho else 'Pendiente'}: {texto}" for texto, hecho in r['lista']],
        'comparacion': comparacion,
        'pendientes': pendientes,
        'reflexion': [(pregunta, reflexion.get(pid)) for pid, pregunta, _ayuda in cierre.PREGUNTAS
                      if reflexion.get(pid)],
    }


def _resumen_avance(n):
    return (f"Comprobaciones atendidas: {n['atendidas']} de {n['total']} "
            f"(por adaptar: {n['pendiente']}; sin revisar: {n['sin_revisar']}).")


def _resumen_verificacion(n):
    return (f"Comprobaciones verificadas: {n['confirmadas'] + n['hallazgos']} de {n['total']} "
            f"(se confirman: {n['confirmadas']}; con problema: {n['hallazgos']}).")


def _linea_verificacion(c, nombre, resultado, metodo, nota):
    texto = f'{c} {nombre}: {resultado}'
    if metodo:
        texto += f' (método: {metodo})'
    return texto + (f'. Nota: {nota}' if nota else '.')


def a_markdown(curso):
    d = construir(curso)
    L = [f"# {d['titulo']}", '', f"Fecha: {d['fecha']}", '']
    if d['contexto']:
        L += ['## Contexto del curso', ''] + [f'- {k}: {v}' for k, v in d['contexto']] + ['']
    if d['observaciones']:
        L += ['Qué se busca mejorar:', '', d['observaciones'], '']
    r = d['resultado']
    if r:
        L += ['## Resultado del diagnóstico', '']
        L += [f"- {p['nombre']}: {p['porcentaje']} % ({p['si']} de {p['total']} afirmaciones con «Sí»)"
              for p in r['principios']]
        if r['sugerencias']:
            L += ['', 'Primeras mejoras sugeridas:', '']
            L += [f"{n}. {s['texto']} {s['accion']}" for n, s in enumerate(r['sugerencias'], 1)]
        L.append('')
    L += ['## Unidades', '']
    if not d['unidades']:
        L += ['Aún no se han agregado unidades.', '']
    for n, u in enumerate(d['unidades'], 1):
        L += [f"### Unidad {n}: {u['nombre']}", '']
        if u['aprendizaje']:
            L += [f"Aprendizaje esperado: {u['aprendizaje']}", '']
        L += [f"Decisiones tomadas: {u['tomadas']} de {TOTAL_DECISIONES}", '']
        for principio, filas in u['principios']:
            L += [f'#### {principio}', '']
            for pregunta, etiquetas in filas:
                L.append(f'- {pregunta} ' + ('; '.join(etiquetas) if etiquetas else 'Sin decidir todavía.'))
            L.append('')
        if u['adaptacion'] is not None:
            L += ['#### Adaptación con WCAG 2.2', '', _resumen_avance(u['avance']), '']
            for material, filas in u['adaptacion']:
                L += [f'##### {material}', '']
                L += [f'- {c} {nombre} (nivel {nivel}): {que} Estado: {estado}.'
                      for c, nombre, nivel, que, estado in filas]
                L.append('')
        if u['verificacion']:
            L += ['#### Verificación', '', _resumen_verificacion(u['avance_verificacion']), '']
            for material, filas in u['verificacion']:
                L += [f'##### {material}', '']
                L += [f'- {_linea_verificacion(*f)}' for f in filas]
                L.append('')
        if u['notas']:
            L += ['Notas:', '', u['notas'], '']
    c = d['cierre']
    if c:
        L += ['## Cierre y resumen', '', f"Fecha de cierre: {c['fecha']}", '', '### Resumen del recorrido', '']
        L += [f'- {x}' for x in c['recorrido']] + ['', '### Lista para cerrar', '']
        L += [f'- {x}' for x in c['lista']] + ['']
        if c['comparacion']:
            L += ['### Diagnóstico: antes y después', '']
            L += [f'- {x}' for x in c['comparacion']] + ['']
        if c['pendientes']:
            L += ['### Problemas pendientes de corregir', '']
            L += [f'- {x}' for x in c['pendientes']] + ['']
        L += ['### Reflexión', '']
        for pregunta, respuesta in c['reflexion']:
            L += [f'**{pregunta}**', '', respuesta, '']
        if not c['reflexion']:
            L += ['Sin reflexión registrada.', '']
    L += ['---', AVISO, '']
    return '\n'.join(L)


def _idioma(doc, codigo='es-MX'):
    """Declara el idioma del documento (estilo Normal y valores por defecto)."""
    rpr = doc.styles['Normal'].element.get_or_add_rPr()
    lang = rpr.find(qn('w:lang'))
    if lang is None:
        lang = OxmlElement('w:lang')
        rpr.append(lang)
    lang.set(qn('w:val'), codigo)


def a_docx(curso):
    d = construir(curso)
    doc = Document()
    _idioma(doc)
    doc.core_properties.title = d['titulo']
    doc.core_properties.language = 'es-MX'
    doc.core_properties.author = 'Ecosistema Digital Educativo Inclusivo (UAA)'

    doc.add_heading(d['titulo'], level=0)
    doc.add_paragraph(f"Fecha: {d['fecha']}")

    if d['contexto']:
        doc.add_heading('Contexto del curso', level=1)
        for k, v in d['contexto']:
            doc.add_paragraph(f'{k}: {v}', style='List Bullet')
    if d['observaciones']:
        doc.add_paragraph('Qué se busca mejorar:')
        doc.add_paragraph(d['observaciones'])

    r = d['resultado']
    if r:
        doc.add_heading('Resultado del diagnóstico', level=1)
        for p in r['principios']:
            doc.add_paragraph(f"{p['nombre']}: {p['porcentaje']} % ({p['si']} de {p['total']} afirmaciones con «Sí»)",
                              style='List Bullet')
        if r['sugerencias']:
            doc.add_paragraph('Primeras mejoras sugeridas:')
            for s in r['sugerencias']:
                doc.add_paragraph(f"{s['texto']} {s['accion']}", style='List Number')

    doc.add_heading('Unidades', level=1)
    if not d['unidades']:
        doc.add_paragraph('Aún no se han agregado unidades.')
    for n, u in enumerate(d['unidades'], 1):
        doc.add_heading(f"Unidad {n}: {u['nombre']}", level=2)
        if u['aprendizaje']:
            doc.add_paragraph(f"Aprendizaje esperado: {u['aprendizaje']}")
        doc.add_paragraph(f"Decisiones tomadas: {u['tomadas']} de {TOTAL_DECISIONES}")
        for principio, filas in u['principios']:
            doc.add_heading(principio, level=3)
            for pregunta, etiquetas in filas:
                texto = '; '.join(etiquetas) if etiquetas else 'Sin decidir todavía.'
                doc.add_paragraph(f'{pregunta} {texto}', style='List Bullet')
        if u['adaptacion'] is not None:
            doc.add_heading('Adaptación con WCAG 2.2', level=3)
            doc.add_paragraph(_resumen_avance(u['avance']))
            for material, filas in u['adaptacion']:
                doc.add_heading(material, level=4)
                for c, nombre, nivel, que, estado in filas:
                    doc.add_paragraph(f'{c} {nombre} (nivel {nivel}): {que} Estado: {estado}.',
                                      style='List Bullet')
        if u['verificacion']:
            doc.add_heading('Verificación', level=3)
            doc.add_paragraph(_resumen_verificacion(u['avance_verificacion']))
            for material, filas in u['verificacion']:
                doc.add_heading(material, level=4)
                for f in filas:
                    doc.add_paragraph(_linea_verificacion(*f), style='List Bullet')
        if u['notas']:
            doc.add_paragraph('Notas:')
            doc.add_paragraph(u['notas'])

    c = d['cierre']
    if c:
        doc.add_heading('Cierre y resumen', level=1)
        doc.add_paragraph(f"Fecha de cierre: {c['fecha']}")
        secciones = [('Resumen del recorrido', c['recorrido']), ('Lista para cerrar', c['lista']),
                     ('Diagnóstico: antes y después', c['comparacion']),
                     ('Problemas pendientes de corregir', c['pendientes'])]
        for titulo, lineas in secciones:
            if lineas:
                doc.add_heading(titulo, level=2)
                for x in lineas:
                    doc.add_paragraph(x, style='List Bullet')
        doc.add_heading('Reflexión', level=2)
        for pregunta, respuesta in c['reflexion']:
            doc.add_heading(pregunta, level=3)
            doc.add_paragraph(respuesta)
        if not c['reflexion']:
            doc.add_paragraph('Sin reflexión registrada.')

    doc.add_paragraph(AVISO)
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
