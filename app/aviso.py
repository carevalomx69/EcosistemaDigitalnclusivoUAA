"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Datos del aviso de privacidad y reglas de aceptación.

El texto del aviso es un borrador de trabajo del prototipo. Debe ser revisado por la
instancia universitaria competente antes de usar la plataforma con personas reales.
Los datos institucionales se configuran con variables de entorno:
  AVISO_RESPONSABLE, AVISO_CONTACTO, AVISO_ALOJAMIENTO, AVISO_CONSERVACION
  AVISO_BORRADOR=0   oculta la advertencia de borrador cuando el texto esté aprobado.
No depende de Flask.
"""
import os

# Cambiar esta versión obliga a todas las personas a aceptar de nuevo el aviso.
VERSION_AVISO = '2026-10-borrador-1'

PENDIENTE = '[por definir antes del piloto]'


def contexto_aviso():
    return {
        'version': VERSION_AVISO,
        'borrador': os.environ.get('AVISO_BORRADOR', '1') != '0',
        'responsable': os.environ.get('AVISO_RESPONSABLE') or PENDIENTE,
        'contacto': os.environ.get('AVISO_CONTACTO') or PENDIENTE,
        'alojamiento': os.environ.get('AVISO_ALOJAMIENTO') or PENDIENTE,
        'conservacion': os.environ.get('AVISO_CONSERVACION') or PENDIENTE,
    }


def aviso_al_dia(usuario):
    """True si la persona aceptó la versión vigente del aviso."""
    return bool(usuario.aviso_aceptado_en) and usuario.aviso_version == VERSION_AVISO
