"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Ruta docente, paso 3: creación o adaptación de materiales con criterios WCAG 2.2.

Catálogo de comprobaciones por tipo de material. Cada comprobación remite a un
criterio de éxito de WCAG 2.2 (W3C, 2023) de nivel A o AA, redactado como una
acción concreta para quien prepara el material. Los tipos de material se sugieren
a partir de las decisiones de la unidad (paso 2). Es una lista de trabajo, no una
auditoría de conformidad. No depende de Flask.
"""

# Cada comprobación: (id, criterio, nombre del criterio, nivel, qué revisar, cómo hacerlo)
MATERIALES = (
    {
        'id': 'documento',
        'nombre': 'Documentos y páginas de texto',
        'descripcion': 'Apuntes, lecturas, instrucciones, rúbricas, presentaciones, PDF y páginas en la plataforma.',
        'comprobaciones': (
            ('doc_titulos', '1.3.1', 'Información y relaciones', 'A',
             'Los títulos usan los estilos de título del editor y las listas son listas reales.',
             'En Word o Google Docs aplica «Título 1», «Título 2»… en lugar de solo agrandar o poner en negritas.'),
            ('doc_encabezados', '2.4.6', 'Encabezados y etiquetas', 'AA',
             'Cada título describe el tema de la sección que introduce.',
             'Lee solo los títulos: deberían bastar para saber de qué trata el documento.'),
            ('doc_alt', '1.1.1', 'Contenido no textual', 'A',
             'Cada imagen informativa tiene texto alternativo; las decorativas se marcan como decorativas.',
             'Clic derecho en la imagen › «Ver texto alternativo». Describe la función, no el aspecto.'),
            ('doc_contraste', '1.4.3', 'Contraste (mínimo)', 'AA',
             'El texto tiene un contraste de al menos 4.5:1 con su fondo (3:1 si es texto grande).',
             'Usa un verificador de contraste, como el de WebAIM o Colour Contrast Analyser.'),
            ('doc_color', '1.4.1', 'Uso del color', 'A',
             'Ninguna información depende solo del color.',
             'Evita indicaciones como «lo marcado en rojo»; añade texto, símbolos o subrayado.'),
            ('doc_enlaces', '2.4.4', 'Propósito de los enlaces (en contexto)', 'A',
             'El texto de cada enlace dice a dónde lleva.',
             'Sustituye «clic aquí» o la dirección completa por un texto como «Rúbrica del proyecto (PDF)».'),
            ('doc_idioma', '3.1.1', 'Idioma de la página', 'A',
             'El idioma del documento está configurado como español.',
             'En Word: Revisar › Idioma. En un PDF: Propiedades del documento › Avanzadas.'),
            ('doc_orden', '1.3.2', 'Secuencia significativa', 'A',
             'El orden de lectura es lógico, también en PDF y en diapositivas.',
             'En PowerPoint revisa el «Panel de selección»; en un PDF, el panel de orden de lectura.'),
            ('doc_texto_real', '1.4.5', 'Imágenes de texto', 'AA',
             'El texto es texto real y seleccionable, no una imagen ni un escaneo.',
             'Si solo tienes un escaneo, aplica reconocimiento de texto (OCR) y revisa el resultado.'),
        ),
    },
    {
        'id': 'imagen',
        'nombre': 'Esquemas, infografías y diagramas',
        'descripcion': 'Mapas conceptuales, diagramas de flujo, gráficas e infografías.',
        'comprobaciones': (
            ('img_alt', '1.1.1', 'Contenido no textual', 'A',
             'Tiene un texto alternativo breve que dice qué muestra y para qué sirve.',
             'Una o dos frases. Ejemplo: «Diagrama de flujo del ciclo while: evalúa la condición y repite».'),
            ('img_descripcion', '1.1.1', 'Contenido no textual', 'A',
             'Si es compleja, hay una descripción en texto cercana con la misma información.',
             'Para un esquema, una lista anidada; para una gráfica, una tabla con los datos.'),
            ('img_color', '1.4.1', 'Uso del color', 'A',
             'Las categorías se distinguen por algo más que el color.',
             'Añade etiquetas, formas, patrones o líneas de distinto estilo.'),
            ('img_contraste_no_textual', '1.4.11', 'Contraste no textual', 'AA',
             'Las líneas, flechas y partes necesarias para entenderla tienen un contraste de al menos 3:1.',
             'Revisa sobre todo los colores claros y los fondos con degradado.'),
            ('img_contraste_texto', '1.4.3', 'Contraste (mínimo)', 'AA',
             'El texto dentro de la imagen tiene un contraste de al menos 4.5:1.',
             'Evita texto sobre fotografías o fondos con mucho detalle.'),
            ('img_texto', '1.4.5', 'Imágenes de texto', 'AA',
             'Todo el texto que aparece en la imagen también está disponible como texto real.',
             'Incluye ese texto en la descripción o en el cuerpo del documento.'),
        ),
    },
    {
        'id': 'video',
        'nombre': 'Videos',
        'descripcion': 'Clases grabadas, cápsulas, tutoriales y videos de terceros.',
        'comprobaciones': (
            ('vid_subtitulos', '1.2.2', 'Subtítulos (grabado)', 'A',
             'Tiene subtítulos sincronizados y revisados, no solo automáticos.',
             'Los subtítulos automáticos son un borrador: corrige nombres, términos técnicos y puntuación.'),
            ('vid_audiodescripcion', '1.2.5', 'Audiodescripción (grabado)', 'AA',
             'Lo que solo se ve (pizarrón, código en pantalla, gráficas) también se dice en voz.',
             'Al grabar, narra lo que haces: «escribo la condición i menor que 10».'),
            ('vid_destellos', '2.3.1', 'Umbral de tres destellos o menos', 'A',
             'No hay nada que destelle más de tres veces por segundo.',
             'Revisa transiciones, animaciones y fragmentos de terceros.'),
            ('vid_control_audio', '1.4.2', 'Control del audio', 'A',
             'No se reproduce solo con sonido o, si lo hace, se puede pausar o silenciar.',
             'Desactiva la reproducción automática al insertarlo en la plataforma.'),
            ('vid_teclado', '2.1.1', 'Teclado', 'A',
             'El reproductor se puede usar solo con el teclado.',
             'Prueba con Tab, Espacio y las flechas que puedes reproducir, pausar y activar los subtítulos.'),
        ),
    },
    {
        'id': 'audio',
        'nombre': 'Audios y pódcast',
        'descripcion': 'Grabaciones de voz, pódcast y explicaciones en audio.',
        'comprobaciones': (
            ('aud_transcripcion', '1.2.1', 'Solo audio y solo video (grabado)', 'A',
             'Hay una transcripción en texto con todo lo que se dice e indica quién habla.',
             'Puedes partir de una transcripción automática, pero revísala completa.'),
            ('aud_control', '1.4.2', 'Control del audio', 'A',
             'No se reproduce solo o, si lo hace, se puede pausar o silenciar.',
             'Desactiva la reproducción automática al insertarlo en la plataforma.'),
            ('aud_teclado', '2.1.1', 'Teclado', 'A',
             'El reproductor se puede usar solo con el teclado.',
             'Prueba con Tab, Espacio y las flechas.'),
        ),
    },
    {
        'id': 'actividad',
        'nombre': 'Actividades y cuestionarios en línea',
        'descripcion': 'Cuestionarios, foros, entregas, formularios y herramientas interactivas.',
        'comprobaciones': (
            ('act_instrucciones', '3.3.2', 'Etiquetas o instrucciones', 'A',
             'Cada pregunta o campo tiene instrucciones claras, incluido el formato esperado.',
             'Ejemplo: «Fecha (dd/mm/aaaa)» o «Sube un archivo PDF de máximo 10 MB».'),
            ('act_errores', '3.3.1', 'Identificación de errores', 'A',
             'Si falta algo o hay un error, se indica en texto cuál es y por qué.',
             'Prueba enviar la actividad incompleta y lee el mensaje que aparece.'),
            ('act_teclado', '2.1.1', 'Teclado', 'A',
             'Se puede completar solo con el teclado.',
             'Recórrela con Tab, Mayús+Tab, Espacio, Enter y las flechas, sin usar el ratón.'),
            ('act_foco_visible', '2.4.7', 'Foco visible', 'AA',
             'Siempre se ve en qué elemento está el foco del teclado.',
             'Durante la prueba con teclado, nunca debes perder de vista dónde estás.'),
            ('act_foco_no_oculto', '2.4.11', 'Foco no oculto (mínimo)', 'AA',
             'El elemento con foco no queda tapado por barras fijas, avisos o ventanas.',
             'Criterio nuevo en WCAG 2.2. Revisa avisos de cookies y menús que se quedan fijos.'),
            ('act_tiempo', '2.2.1', 'Tiempo ajustable', 'A',
             'Si hay límite de tiempo, se puede ampliar o hay un procedimiento claro para pedirlo.',
             'Configura tiempo adicional por persona en la plataforma y explica cómo solicitarlo.'),
            ('act_objetivo', '2.5.8', 'Tamaño del objetivo (mínimo)', 'AA',
             'Los botones, casillas y enlaces miden al menos 24 por 24 píxeles o tienen espacio alrededor.',
             'Criterio nuevo en WCAG 2.2. Revísalo en el celular: no deberías tocar uno por error.'),
            ('act_arrastre', '2.5.7', 'Movimientos de arrastre', 'AA',
             'Las actividades de arrastrar y soltar tienen una alternativa con clics o teclado.',
             'Criterio nuevo en WCAG 2.2. Si la herramienta no la tiene, ofrece una versión con opciones.'),
            ('act_redundante', '3.3.7', 'Entrada redundante', 'A',
             'No se pide de nuevo información que ya se dio en el mismo proceso.',
             'Criterio nuevo en WCAG 2.2. Por ejemplo, no pedir otra vez la matrícula en cada paso.'),
            ('act_autenticacion', '3.3.8', 'Autenticación accesible (mínimo)', 'AA',
             'Entrar no exige resolver acertijos ni transcribir códigos; se permite pegar la contraseña.',
             'Criterio nuevo en WCAG 2.2. Evita herramientas externas con captchas de imágenes.'),
            ('act_ayuda', '3.2.6', 'Ayuda consistente', 'A',
             'El medio para pedir ayuda está en el mismo lugar en cada actividad.',
             'Criterio nuevo en WCAG 2.2. Por ejemplo, un enlace fijo al foro de dudas al final de cada actividad.'),
        ),
    },
)

ESTADOS = (
    ('cumple', 'Ya se cumple'),
    ('pendiente', 'Por adaptar'),
    ('no_aplica', 'No aplica'),
)
ETIQUETA_ESTADO = dict(ESTADOS)
ETIQUETA_ESTADO['sin_revisar'] = 'Sin revisar'

POR_ID = {m['id']: m for m in MATERIALES}
COMPROBACIONES_VALIDAS = {m['id']: {c[0] for c in m['comprobaciones']} for m in MATERIALES}

# Opciones del plan (paso 2) que implican preparar un tipo de material
SUGERENCIAS_DEL_PLAN = {
    ('rep_formatos', 'texto'): 'documento',
    ('rep_formatos', 'ejemplo'): 'documento',
    ('rep_formatos', 'esquema'): 'imagen',
    ('rep_formatos', 'video'): 'video',
    ('rep_formatos', 'audio'): 'audio',
    ('rep_apoyos', 'glosario'): 'documento',
    ('rep_apoyos', 'pdf'): 'documento',
    ('acc_claridad', 'rubrica'): 'documento',
    ('acc_claridad', 'pasos'): 'documento',
    ('acc_acceso', 'probar'): 'actividad',
    ('imp_retro', 'autoevaluacion'): 'actividad',
}


def materiales_sugeridos(elegidas_plan):
    """Tipos de material que se desprenden de las decisiones de la unidad, en orden del catálogo."""
    ids = {mid for (decision, valor), mid in SUGERENCIAS_DEL_PLAN.items()
           if valor in elegidas_plan.get(decision, [])}
    return [m['id'] for m in MATERIALES if m['id'] in ids]


def limpiar(materiales, estados):
    """Deja solo materiales, comprobaciones y estados que existen en el catálogo.
    Las comprobaciones de un material no elegido se descartan."""
    materiales = [m['id'] for m in MATERIALES if m['id'] in set(materiales)]
    validos = {e for e, _ in ESTADOS}
    limpio = {}
    for mid in materiales:
        for cid in COMPROBACIONES_VALIDAS[mid]:
            if estados.get(cid) in validos:
                limpio[cid] = estados[cid]
    return {'materiales': materiales, 'estados': limpio}


def _materiales_validos(adaptacion):
    """Materiales guardados que siguen existiendo en el catálogo."""
    return [mid for mid in adaptacion.get('materiales', []) if mid in POR_ID]


def avance(adaptacion):
    """Conteo por estado sobre las comprobaciones de los materiales elegidos.
    «Atendidas» son las que se cumplen o no aplican."""
    conteo = {'total': 0, 'cumple': 0, 'pendiente': 0, 'no_aplica': 0, 'sin_revisar': 0}
    estados = adaptacion.get('estados', {})
    for mid in _materiales_validos(adaptacion):
        for c in POR_ID[mid]['comprobaciones']:
            conteo['total'] += 1
            conteo[estados.get(c[0], 'sin_revisar')] += 1
    conteo['atendidas'] = conteo['cumple'] + conteo['no_aplica']
    return conteo


def detalle(adaptacion):
    """Estructura legible para exportar: por material, lista de (criterio, nombre, nivel, qué revisar, estado)."""
    estados = adaptacion.get('estados', {})
    salida = []
    for mid in _materiales_validos(adaptacion):
        m = POR_ID[mid]
        filas = [(c[1], c[2], c[3], c[4], ETIQUETA_ESTADO[estados.get(c[0], 'sin_revisar')])
                 for c in m['comprobaciones']]
        salida.append((m['nombre'], filas))
    return salida
