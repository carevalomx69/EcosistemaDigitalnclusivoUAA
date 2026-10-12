"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Punto de entrada del servidor de desarrollo

Uso:
    python run.py

El servidor arranca en http://127.0.0.1:5000
El modo debug recarga automáticamente al guardar cualquier archivo.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA")
    print("  Doctorado en Ciencias Aplicadas de la Computación")
    print("=" * 60)
    print()
    print("  Servidor disponible en: http://127.0.0.1:5000")
    print()
    print("  Credenciales de prueba:")
    print("    Admin:   admin@uaa.mx  /  admin2025")
    print("    Docente: docente@uaa.mx / docente2025")
    print("    Alumno:  alumno@uaa.mx  / alumno2025")
    print()
    print("  Ejecuta 'python seed.py' para cargar datos de prueba.")
    print("  Detén el servidor con Ctrl+C")
    print("=" * 60)
    print()
    app.run(debug=True, host='127.0.0.1', port=5000)
