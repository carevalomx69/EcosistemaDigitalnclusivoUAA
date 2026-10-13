"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Ruta docente, paso 2: planeación con DUA.

Catálogo de decisiones de diseño por unidad, organizadas por los tres principios
del DUA 3.0 (CAST, 2024). Cada opción puede estar ligada a una afirmación del
diagnóstico (paso 1): si en el diagnóstico esa afirmación no se respondió «Sí»,
la opción se marca como sugerida. Es una propuesta de trabajo, no un instrumento
validado. No depende de Flask.
"""

# Cada decisión: id, pregunta y opciones (valor, etiqueta, afirmación del diagnóstico o None)
PRINCIPIOS_PLAN = (
    {
        'id': 'representacion',
        'nombre': 'Representación',
        'decisiones': (
            {'id': 'rep_formatos',
             'pregunta': '¿En qué formatos presentarás lo esencial de esta unidad?',
             'opciones': (
                 ('texto', 'Texto con títulos y listas reales', 'r1'),
                 ('esquema', 'Esquema o infografía con descripción en texto', 'r2'),
                 ('video', 'Video con subtítulos', 'r3'),
                 ('audio', 'Audio con transcripción', 'r3'),
                 ('ejemplo', 'Ejemplo resuelto o demostración', 'r6'),
             )},
            {'id': 'rep_apoyos',
             'pregunta': '¿Qué apoyos darás para comprender el contenido?',
             'opciones': (
                 ('glosario', 'Glosario de términos clave', None),
                 ('previos', 'Actividad para activar conocimientos previos', None),
                 ('pdf', 'Documentos descargables con texto seleccionable', 'r4'),
                 ('contraste', 'Revisión de contraste y de uso del color', 'r5'),
             )},
        ),
    },
    {
        'id': 'accion_expresion',
        'nombre': 'Acción y expresión',
        'decisiones': (
            {'id': 'acc_evidencias',
             'pregunta': '¿De qué maneras podrán mostrar lo que aprendieron?',
             'opciones': (
                 ('escrito', 'Producto escrito', 'a1'),
                 ('oral', 'Exposición o explicación oral', 'a1'),
                 ('visual', 'Producto visual (mapa, diagrama o cartel)', 'a1'),
                 ('proyecto', 'Proyecto o práctica', 'a1'),
                 ('portafolio', 'Portafolio con evidencias', 'a1'),
             )},
            {'id': 'acc_claridad',
             'pregunta': '¿Qué harás para que cada actividad sea clara?',
             'opciones': (
                 ('rubrica', 'Compartir la rúbrica antes de empezar', 'a2'),
                 ('ejemplo_entrega', 'Mostrar un ejemplo de entrega', 'a2'),
                 ('pasos', 'Dar los pasos y las fechas por escrito', 'a2'),
             )},
            {'id': 'acc_acceso',
             'pregunta': '¿Cómo cuidarás el acceso a las herramientas y a los tiempos?',
             'opciones': (
                 ('probar', 'Probar la herramienta con teclado y lector de pantalla', 'a3'),
                 ('alternativa', 'Ofrecer una alternativa si la herramienta falla', 'a3'),
                 ('tiempos', 'Definir cómo pedir ajuste de tiempos', 'a4'),
             )},
        ),
    },
    {
        'id': 'implicacion',
        'nombre': 'Implicación',
        'decisiones': (
            {'id': 'imp_proposito',
             'pregunta': '¿Cómo darás sentido a la unidad?',
             'opciones': (
                 ('proposito', 'Propósito de la unidad en dos líneas', 'i1'),
                 ('carrera', 'Relación con la carrera o la práctica profesional', 'i1'),
                 ('caso', 'Un caso real como punto de partida', None),
             )},
            {'id': 'imp_eleccion',
             'pregunta': '¿Qué margen de elección ofrecerás?',
             'opciones': (
                 ('tema', 'Elegir el tema', 'i2'),
                 ('formato', 'Elegir el formato de entrega', 'i2'),
                 ('orden', 'Elegir el orden de trabajo', 'i2'),
                 ('ritmo', 'Elegir el ritmo dentro de un rango de fechas', 'i2'),
             )},
            {'id': 'imp_retro',
             'pregunta': '¿Cómo acompañarás el avance?',
             'opciones': (
                 ('mitad', 'Retroalimentación a mitad de la unidad', 'i3'),
                 ('acierto_mejora', 'Comentario con un acierto y una mejora concreta', 'i3'),
                 ('autoevaluacion', 'Autoevaluación con la rúbrica', 'i3'),
                 ('apoyos', 'Informar y canalizar a los apoyos institucionales', 'i4'),
             )},
        ),
    },
)

DECISIONES = tuple(d for p in PRINCIPIOS_PLAN for d in p['decisiones'])
TOTAL_DECISIONES = len(DECISIONES)
OPCIONES_VALIDAS = {d['id']: {o[0] for o in d['opciones']} for d in DECISIONES}
MAX_UNIDADES = 20


def limpiar(datos):
    """Deja solo decisiones y opciones que existen en el catálogo."""
    limpio = {}
    for did, validas in OPCIONES_VALIDAS.items():
        elegidas = [v for v in datos.get(did, []) if v in validas]
        if elegidas:
            limpio[did] = sorted(set(elegidas))
    return limpio


def decisiones_tomadas(elegidas):
    """Cuántas decisiones tienen al menos una opción elegida."""
    return sum(1 for d in DECISIONES if elegidas.get(d['id']))


def sugeridas(respuestas_diagnostico):
    """Ids de afirmaciones del diagnóstico que no se respondieron «Sí»."""
    return {k for k, v in respuestas_diagnostico.items() if v != 'si'}


def etiquetas_elegidas(elegidas):
    """Estructura legible para exportar: por principio, lista de (pregunta, [etiquetas])."""
    salida = []
    for p in PRINCIPIOS_PLAN:
        filas = []
        for d in p['decisiones']:
            marcadas = elegidas.get(d['id'], [])
            etiquetas = [o[1] for o in d['opciones'] if o[0] in marcadas]
            filas.append((d['pregunta'], etiquetas))
        salida.append((p['nombre'], filas))
    return salida
