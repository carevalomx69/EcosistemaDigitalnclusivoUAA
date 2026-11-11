"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Ruta docente, paso 5: cierre y resumen.

Reúne el recorrido de un curso (diagnóstico, planeación, adaptación y verificación),
compara el diagnóstico inicial con el más reciente, indica qué falta para cerrar y
guarda la reflexión de la persona docente. No depende de Flask: recibe el curso y
usa los catálogos de los pasos anteriores.
"""
from app import adaptacion, verificacion
from app.diagnostico import evaluar
from app.planeacion import TOTAL_DECISIONES, decisiones_tomadas

PREGUNTAS = (
    ('logros', '¿Qué funcionó en este recorrido?',
     'Por ejemplo, un cambio que notaste en tus materiales o en la participación del grupo.'),
    ('dificultades', '¿Qué fue difícil o quedó pendiente?',
     'Por ejemplo, falta de tiempo, una herramienta que no es accesible o una duda sin resolver.'),
    ('siguiente', '¿Qué harás en el siguiente ciclo del curso?',
     'Uno o dos compromisos concretos y realistas.'),
)
IDS_PREGUNTAS = tuple(p[0] for p in PREGUNTAS)
MAX_RESPUESTA = 1000


def _sumar(conteos, claves):
    return {k: sum(c[k] for c in conteos) for k in claves}


def comparacion(inicial, actual):
    """Porcentaje por principio antes y después. None si no hay diagnóstico inicial distinto."""
    if not inicial or inicial == actual:
        return None
    antes, despues = evaluar(inicial)['principios'], evaluar(actual)['principios']
    return [{'nombre': a['nombre'], 'antes': a['porcentaje'], 'despues': d['porcentaje'],
             'cambio': d['porcentaje'] - a['porcentaje']} for a, d in zip(antes, despues)]


def resumen(curso):
    """Resumen del recorrido del curso con los datos de los cuatro pasos."""
    unidades = list(curso.unidades)
    paso3 = [adaptacion.avance(u.adaptacion) for u in unidades]
    paso4 = [verificacion.avance(u.adaptacion, u.verificacion) for u in unidades]
    tomadas = [decisiones_tomadas(u.elegidas) for u in unidades]
    hallazgos = [(u.nombre, h) for u in unidades for h in verificacion.hallazgos(u.adaptacion, u.verificacion)]
    r = {
        'diagnostico': evaluar(curso.respuestas_diagnostico),
        'comparacion': comparacion(curso.respuestas_diagnostico_inicial, curso.respuestas_diagnostico),
        'unidades': len(unidades),
        'decisiones': {'tomadas': sum(tomadas), 'total': TOTAL_DECISIONES * len(unidades)},
        'adaptacion': _sumar(paso3, ('total', 'cumple', 'pendiente', 'no_aplica', 'sin_revisar', 'atendidas')),
        'verificacion': _sumar(paso4, ('total', 'confirmadas', 'hallazgos', 'sin_verificar')),
        'metodos': verificacion.metodos_usados([u.verificacion for u in unidades]),
        'hallazgos': hallazgos,
    }
    r['lista'] = (
        ('Diagnóstico del curso respondido', curso.tiene_diagnostico),
        ('Al menos una unidad planeada', bool(unidades)),
        ('Decisiones DUA en todas las unidades', bool(unidades) and all(tomadas)),
        ('Materiales revisados con WCAG 2.2 en todas las unidades', bool(unidades) and all(u.adaptacion for u in unidades)),
        ('Al menos una comprobación verificada', r['verificacion']['confirmadas'] + r['verificacion']['hallazgos'] > 0),
        ('Sin problemas pendientes de corregir', not hallazgos),
    )
    r['completos'] = sum(1 for _t, hecho in r['lista'] if hecho)
    return r


def limpiar(datos):
    """Respuestas de la reflexión, recortadas y sin campos desconocidos."""
    return {k: (datos.get(k) or '').strip()[:MAX_RESPUESTA] for k in IDS_PREGUNTAS}
