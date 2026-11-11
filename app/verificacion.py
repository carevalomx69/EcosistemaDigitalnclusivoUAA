"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Ruta docente, paso 4: verificación de los materiales.

En el paso 3 la persona docente declara qué comprobaciones ya se cumplen. En este
paso las comprueba con un método concreto y registra el resultado: se confirma o se
encontró un problema, con una nota breve. Para cada comprobación se sugiere el
método más adecuado. Las herramientas automáticas detectan solo una parte de los
problemas, por eso se combinan con pruebas manuales. No depende de Flask.
"""
from app.adaptacion import POR_ID

METODOS = (
    ('verificador', 'Verificador automático (Word, PowerPoint, Acrobat, WAVE o axe)'),
    ('revision', 'Revisión manual del material'),
    ('contraste', 'Medición con un verificador de contraste'),
    ('teclado', 'Prueba solo con teclado'),
    ('lector', 'Prueba con lector de pantalla (NVDA, Narrador o VoiceOver)'),
    ('celular', 'Prueba en celular o con ampliación al 200 %'),
    ('reproduccion', 'Reproducción completa del video o audio'),
    ('persona', 'Revisión por otra persona (colega o estudiante voluntario)'),
)
ETIQUETA_METODO = dict(METODOS)

RESULTADOS = (
    ('confirmado', 'Se confirma'),
    ('hallazgo', 'Se encontró un problema'),
)
ETIQUETA_RESULTADO = dict(RESULTADOS)
MAX_NOTA = 300

# Método sugerido para cada comprobación del paso 3
METODO_SUGERIDO = {
    'doc_titulos': 'verificador', 'doc_encabezados': 'revision', 'doc_alt': 'verificador',
    'doc_contraste': 'contraste', 'doc_color': 'revision', 'doc_enlaces': 'revision',
    'doc_idioma': 'verificador', 'doc_orden': 'lector', 'doc_texto_real': 'revision',
    'img_alt': 'lector', 'img_descripcion': 'revision', 'img_color': 'revision',
    'img_contraste_no_textual': 'contraste', 'img_contraste_texto': 'contraste', 'img_texto': 'revision',
    'vid_subtitulos': 'reproduccion', 'vid_audiodescripcion': 'reproduccion', 'vid_destellos': 'reproduccion',
    'vid_control_audio': 'revision', 'vid_teclado': 'teclado',
    'aud_transcripcion': 'reproduccion', 'aud_control': 'revision', 'aud_teclado': 'teclado',
    'act_instrucciones': 'persona', 'act_errores': 'revision', 'act_teclado': 'teclado',
    'act_foco_visible': 'teclado', 'act_foco_no_oculto': 'teclado', 'act_tiempo': 'revision',
    'act_objetivo': 'celular', 'act_arrastre': 'teclado', 'act_redundante': 'revision',
    'act_autenticacion': 'revision', 'act_ayuda': 'revision',
}


def por_verificar(adaptacion):
    """Comprobaciones que el paso 3 marcó como «Ya se cumple», por material y en orden del catálogo."""
    estados = adaptacion.get('estados', {})
    salida = []
    for mid in adaptacion.get('materiales', []):
        if mid not in POR_ID:
            continue
        filas = [c for c in POR_ID[mid]['comprobaciones'] if estados.get(c[0]) == 'cumple']
        if filas:
            salida.append((POR_ID[mid], filas))
    return salida


def limpiar(adaptacion, datos):
    """Registros válidos de verificación: solo de comprobaciones que se declararon cumplidas,
    con método y resultado del catálogo. `datos` responde a get(nombre_de_campo)."""
    limpio = {}
    for _material, filas in por_verificar(adaptacion):
        for c in filas:
            cid = c[0]
            resultado = datos.get(f'res_{cid}')
            if resultado not in ETIQUETA_RESULTADO:
                continue
            metodo = datos.get(f'met_{cid}')
            if metodo not in ETIQUETA_METODO:
                metodo = METODO_SUGERIDO[cid]
            nota = (datos.get(f'nota_{cid}') or '').strip()[:MAX_NOTA]
            limpio[cid] = {'metodo': metodo, 'resultado': resultado, 'nota': nota}
    return limpio


def avance(adaptacion, verificacion):
    """Conteo de la verificación. Solo cuenta registros de comprobaciones que siguen declaradas cumplidas."""
    total = confirmadas = hallazgos = 0
    for _material, filas in por_verificar(adaptacion):
        for c in filas:
            total += 1
            resultado = verificacion.get(c[0], {}).get('resultado')
            confirmadas += resultado == 'confirmado'
            hallazgos += resultado == 'hallazgo'
    return {'total': total, 'confirmadas': confirmadas, 'hallazgos': hallazgos,
            'sin_verificar': total - confirmadas - hallazgos}


def metodos_usados(registros):
    """Cuántas veces se usó cada método en una lista de verificaciones, en orden del catálogo."""
    cuenta = {}
    for v in registros:
        for r in v.values():
            cuenta[r['metodo']] = cuenta.get(r['metodo'], 0) + 1
    return [(ETIQUETA_METODO[m], cuenta[m]) for m, _ in METODOS if m in cuenta]


def hallazgos(adaptacion, verificacion):
    """Problemas encontrados: lista de (criterio, nombre, qué revisar, nota)."""
    return [(c[1], c[2], c[4], verificacion[c[0]]['nota'])
            for _material, filas in por_verificar(adaptacion) for c in filas
            if verificacion.get(c[0], {}).get('resultado') == 'hallazgo']


def detalle(adaptacion, verificacion):
    """Estructura legible para exportar: por material, lista de (criterio, nombre, resultado, método, nota)."""
    salida = []
    for material, filas in por_verificar(adaptacion):
        out = []
        for c in filas:
            r = verificacion.get(c[0])
            if r:
                out.append((c[1], c[2], ETIQUETA_RESULTADO[r['resultado']], ETIQUETA_METODO[r['metodo']], r['nota']))
            else:
                out.append((c[1], c[2], 'Sin verificar', None, ''))
        salida.append((material['nombre'], out))
    return salida
