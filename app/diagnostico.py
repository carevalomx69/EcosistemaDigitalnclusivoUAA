"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Ruta docente, paso 1: diagnóstico del curso.

Instrumento de autoevaluación orientativo. Está organizado con los tres
principios del DUA 3.0 (CAST, 2024) y remite a criterios de WCAG 2.2 cuando
el ítem se refiere a materiales digitales. No es un instrumento validado:
su propósito es ayudar a elegir por dónde empezar. Los ítems se afinarán con
la retroalimentación del piloto con docentes.

Este módulo no depende de Flask, así que se puede probar por separado.
"""

OPCIONES = (
    ('si', 'Sí, en general'),
    ('parcial', 'En parte'),
    ('no', 'No'),
    ('no_se', 'No lo sé'),
)
PUNTOS = {'si': 2, 'parcial': 1, 'no': 0, 'no_se': 0}
VALORES_VALIDOS = tuple(v for v, _ in OPCIONES)

# Cada principio agrupa sus ítems. 'esfuerzo' (1 bajo, 2 medio, 3 alto) sirve
# para sugerir primero las mejoras más fáciles de lograr.
PRINCIPIOS = (
    {
        'id': 'representacion',
        'nombre': 'Representación',
        'descripcion': 'Cómo presento la información para que más personas puedan percibirla y comprenderla.',
        'items': (
            {'id': 'r1', 'esfuerzo': 1, 'criterio': 'WCAG 1.3.1',
             'texto': 'Mis documentos y diapositivas usan títulos y listas reales del programa, no solo negritas o espacios.',
             'accion': 'Aplica los estilos de título y de lista de tu procesador de texto o de tus diapositivas.'},
            {'id': 'r2', 'esfuerzo': 1, 'criterio': 'WCAG 1.1.1',
             'texto': 'Las imágenes, gráficas y diagramas que uso llevan una descripción en texto.',
             'accion': 'Agrega texto alternativo a cada imagen que aporte información y márcala como decorativa si no aporta.'},
            {'id': 'r3', 'esfuerzo': 2, 'criterio': 'WCAG 1.2.1 y 1.2.2',
             'texto': 'Mis videos tienen subtítulos y mis audios tienen transcripción.',
             'accion': 'Activa los subtítulos automáticos de tu plataforma de video y revísalos antes de publicarlos.'},
            {'id': 'r4', 'esfuerzo': 2, 'criterio': 'WCAG 1.3.1 y 4.1.2',
             'texto': 'Mis PDF contienen texto seleccionable y no son fotografías de páginas.',
             'accion': 'Exporta desde el archivo original en lugar de escanear, y comprueba que puedas seleccionar el texto.'},
            {'id': 'r5', 'esfuerzo': 1, 'criterio': 'WCAG 1.4.3 y 1.4.1',
             'texto': 'Mis materiales tienen buen contraste y no usan solo el color para transmitir información.',
             'accion': 'Usa texto oscuro sobre fondo claro y agrega una etiqueta o forma además del color.'},
            {'id': 'r6', 'esfuerzo': 3, 'criterio': 'DUA 1',
             'texto': 'Ofrezco lo esencial de cada tema en más de un formato (texto, audio, video o esquema).',
             'accion': 'Elige un tema clave del curso y prepara una segunda versión en otro formato.'},
        ),
    },
    {
        'id': 'accion_expresion',
        'nombre': 'Acción y expresión',
        'descripcion': 'Cómo permito que el estudiantado participe y muestre lo que aprendió.',
        'items': (
            {'id': 'a1', 'esfuerzo': 2, 'criterio': 'DUA 2',
             'texto': 'Mis estudiantes pueden demostrar lo aprendido de más de una manera (escrita, oral, visual o con un proyecto).',
             'accion': 'En una evaluación, ofrece dos formatos de entrega con la misma rúbrica.'},
            {'id': 'a2', 'esfuerzo': 1, 'criterio': 'WCAG 3.3.2',
             'texto': 'Las instrucciones de cada actividad dicen qué hacer, cómo entregarlo y con qué criterios se evalúa, antes de empezar.',
             'accion': 'Agrega a cada actividad una rúbrica breve y un ejemplo de entrega.'},
            {'id': 'a3', 'esfuerzo': 2, 'criterio': 'WCAG 2.1.1',
             'texto': 'Las herramientas digitales que pido usar se pueden manejar con teclado y con lector de pantalla, o lo he comprobado.',
             'accion': 'Prueba tu herramienta con el tabulador y con un lector de pantalla gratuito antes de pedirla.'},
            {'id': 'a4', 'esfuerzo': 1, 'criterio': 'WCAG 2.2.1',
             'texto': 'Los tiempos de entrega o de examen admiten ajustes razonables sin trámites complicados.',
             'accion': 'Define al inicio del curso cómo solicitar más tiempo y cómo se resuelve.'},
        ),
    },
    {
        'id': 'implicacion',
        'nombre': 'Implicación',
        'descripcion': 'Cómo motivo, oriento y acompaño al estudiantado, incluidos los apoyos institucionales.',
        'items': (
            {'id': 'i1', 'esfuerzo': 1, 'criterio': 'DUA 3',
             'texto': 'Al iniciar cada unidad explico para qué sirve y cómo se relaciona con la carrera.',
             'accion': 'Escribe dos líneas de propósito al inicio de cada unidad.'},
            {'id': 'i2', 'esfuerzo': 2, 'criterio': 'DUA 3',
             'texto': 'Mis estudiantes tienen algún margen de elección (temas, orden de trabajo o formato).',
             'accion': 'Ofrece una opción de tema o de formato en una sola actividad para empezar.'},
            {'id': 'i3', 'esfuerzo': 2, 'criterio': 'DUA 3',
             'texto': 'Doy retroalimentación frecuente y orientada a mejorar, no solo una calificación.',
             'accion': 'Elige una entrega y devuelve un comentario sobre un acierto y una mejora concreta.'},
            {'id': 'i4', 'esfuerzo': 1, 'criterio': 'Mesosistema',
             'texto': 'Conozco los servicios de apoyo de mi institución para estudiantes con discapacidad y sé cómo canalizar a una persona.',
             'accion': 'Averigua qué área ofrece apoyos y anota el contacto en tu programa del curso.'},
        ),
    },
)

TODOS_LOS_ITEMS = tuple(i for p in PRINCIPIOS for i in p['items'])
IDS_ITEMS = tuple(i['id'] for i in TODOS_LOS_ITEMS)


def faltantes(respuestas):
    """Ids de ítems sin una respuesta válida."""
    return [i for i in IDS_ITEMS if respuestas.get(i) not in VALORES_VALIDOS]


def evaluar(respuestas):
    """Calcula el resultado por principio y las acciones sugeridas.

    Devuelve un diccionario con:
      - principios: lista con puntaje (0 a 100), conteos y nombre
      - sugerencias: hasta tres ítems con menor puntaje, desempatando por
        menor esfuerzo, para empezar por las mejoras más sencillas
      - por_explorar: ítems respondidos 'no lo sé'
    """
    principios = []
    for p in PRINCIPIOS:
        total = len(p['items']) * 2
        obtenido = sum(PUNTOS.get(respuestas.get(i['id']), 0) for i in p['items'])
        principios.append({
            'id': p['id'], 'nombre': p['nombre'], 'descripcion': p['descripcion'],
            'porcentaje': round(obtenido / total * 100),
            'si': sum(1 for i in p['items'] if respuestas.get(i['id']) == 'si'),
            'total': len(p['items']),
        })

    pendientes = [i for i in TODOS_LOS_ITEMS if respuestas.get(i['id']) != 'si']
    pendientes.sort(key=lambda i: (PUNTOS.get(respuestas.get(i['id']), 0), i['esfuerzo']))
    nombre_de = {i['id']: p['nombre'] for p in PRINCIPIOS for i in p['items']}
    sugerencias = [dict(i, principio=nombre_de[i['id']], respuesta=respuestas.get(i['id']))
                   for i in pendientes[:3]]
    por_explorar = [i for i in TODOS_LOS_ITEMS if respuestas.get(i['id']) == 'no_se']
    return {'principios': principios, 'sugerencias': sugerencias, 'por_explorar': por_explorar}
