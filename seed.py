"""
ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
Script de datos iniciales (seed)

Uso:
    python seed.py            # carga los datos solo si la base está vacía
    python seed.py --reset    # BORRA toda la base y la vuelve a sembrar

Las cuentas de demostración usan la contraseña de la variable de entorno
DEMO_PASSWORD. En local, si no se define, se usa una contraseña de desarrollo.
Con APP_ENV=production la variable es obligatoria; si falta, no se crean usuarios.

Crea: usuarios de prueba (admin, docente, alumnos), grupos por carrera,
glosario, módulo y una actividad de ejemplo.
"""
import json
import os
import sys

from app import create_app, db
from app.models import Usuario, Grupo, Modulo, SeccionModulo, Actividad, TerminoGlosario

app = create_app()

REINICIAR = '--reset' in sys.argv
EN_PRODUCCION = os.environ.get('APP_ENV') == 'production'
CONTRASENA_DEMO = os.environ.get('DEMO_PASSWORD')

if not CONTRASENA_DEMO:
    if EN_PRODUCCION:
        print("APP_ENV=production y falta DEMO_PASSWORD: no se crean usuarios de demostración.")
        sys.exit(0)
    CONTRASENA_DEMO = 'demo-local-2026'  # solo para ejecución local

with app.app_context():

    if REINICIAR:
        print("Reiniciando base de datos (--reset)...")
        db.drop_all()
    db.create_all()

    if Usuario.query.first() is not None:
        print("La base ya tiene datos; no se vuelve a sembrar. Usa --reset para reiniciar.")
        sys.exit(0)

    # ── GRUPOS ────────────────────────────────────────────────────────────
    print("Creando grupos...")

    g1 = Grupo(nombre='Grupo A — Ingeniería en Software 2025',
               carrera='Ingeniería en Software')
    g2 = Grupo(nombre='Grupo B — Ciencias Computacionales 2025',
               carrera='Licenciatura en Ciencias Computacionales')
    g3 = Grupo(nombre='Grupo C — Sistemas Computacionales 2025',
               carrera='Ingeniería en Sistemas Computacionales')
    g4 = Grupo(nombre='Posgrado — Doctorado Ciencias Computacionales',
               carrera='Doctorado en Ciencias Aplicadas de la Computación')

    db.session.add_all([g1, g2, g3, g4])
    db.session.flush()  # Para obtener los IDs

    # ── USUARIOS ──────────────────────────────────────────────────────────
    print("Creando usuarios de prueba...")

    admin = Usuario(nombre='Admin', apellidos='Demo',
                    correo='admin@demo.example', rol='admin', carrera='posgrado_computo')
    admin.establecer_contrasena(CONTRASENA_DEMO)

    docente = Usuario(nombre='Docente', apellidos='Demo',
                      correo='docente@demo.example', rol='docente', carrera='posgrado_computo',
                      grupo_id=g1.id)
    docente.establecer_contrasena(CONTRASENA_DEMO)

    # Estudiantes con diferentes perfiles de preferencias (representan las condiciones
    # de discapacidad del estudio sin almacenar diagnósticos médicos)
    alumnos = [
        Usuario(nombre='Ana', apellidos='García López',
                correo='alumno@demo.example', rol='estudiante',
                carrera='ing_software', grupo_id=g1.id,
                # Perfil: preferencia por audio (ej: discapacidad visual)
                pref_tamano_texto='normal', pref_contraste='normal',
                pref_velocidad_audio=0.75, pref_formatos='texto,audio'),

        Usuario(nombre='Roberto', apellidos='Hernández Cruz',
                correo='roberto@demo.example', rol='estudiante',
                carrera='ing_software', grupo_id=g1.id,
                # Perfil: texto grande, alto contraste (ej: baja visión)
                pref_tamano_texto='grande', pref_contraste='alto',
                pref_velocidad_audio=1.0, pref_formatos='texto,visual'),

        Usuario(nombre='María', apellidos='Torres Ramírez',
                correo='maria@demo.example', rol='estudiante',
                carrera='lic_computacion', grupo_id=g2.id,
                # Perfil: densidad reducida, sin audio (ej: discapacidad auditiva)
                pref_tamano_texto='normal', pref_contraste='normal',
                pref_densidad='reducida', pref_formatos='texto,video,visual'),

        Usuario(nombre='Luis', apellidos='Jiménez Pérez',
                correo='luis@demo.example', rol='estudiante',
                carrera='lic_computacion', grupo_id=g2.id,
                # Perfil: texto muy grande, densidad reducida (ej: TDAH)
                pref_tamano_texto='muy_grande', pref_contraste='normal',
                pref_densidad='reducida', pref_formatos='texto'),

        Usuario(nombre='Sofía', apellidos='Vega Morales',
                correo='sofia@demo.example', rol='estudiante',
                carrera='ing_sistemas', grupo_id=g3.id,
                # Perfil: normal (ej: discapacidad del habla — prefiere texto/visual)
                pref_tamano_texto='normal', pref_contraste='normal',
                pref_formatos='texto,visual'),
    ]
    for a in alumnos:
        a.establecer_contrasena(CONTRASENA_DEMO)

    db.session.add(admin)
    db.session.add(docente)
    db.session.add_all(alumnos)

    # Asignar docente a grupos
    g1.docente_id = docente.id
    g2.docente_id = docente.id

    # ── GLOSARIO ──────────────────────────────────────────────────────────
    print("Creando glosario...")

    terminos = [
        TerminoGlosario(termino='DUA',
            definicion='Diseño Universal para el Aprendizaje (v3.0, CAST 2024). Marco pedagógico que propone diseñar entornos educativos anticipando la diversidad de los aprendices desde el origen, ofreciendo múltiples formas de representación, acción, expresión e implicación.'),
        TerminoGlosario(termino='WCAG',
            definicion='Web Content Accessibility Guidelines. Pautas del W3C para el diseño accesible de contenidos web. La versión 2.2 (2023) es el estándar actual con criterios de éxito organizados en tres niveles: A, AA y AAA.'),
        TerminoGlosario(termino='POUR',
            definicion='Acrónimo de los cuatro principios de WCAG 2.2: Perceptible (el contenido debe poder presentarse de formas que los usuarios puedan percibir), Operable (los componentes deben ser operables), Comprensible (la información debe ser comprensible) y Robusto (el contenido debe ser suficientemente robusto para ser interpretado por tecnologías asistivas).'),
        TerminoGlosario(termino='Ecosistema digital',
            definicion='Conjunto articulado de actores, tecnologías, prácticas pedagógicas, políticas institucionales y contextos socioculturales que interactúan de manera dinámica para configurar la experiencia educativa digital de manera interdependiente.'),
        TerminoGlosario(termino='Microsistema',
            definicion='En el modelo de Bronfenbrenner, el entorno inmediato de interacción del individuo. En el contexto digital educativo: la interfaz de la plataforma, el perfil del usuario, las actividades de aprendizaje y la relación directa con los contenidos.'),
        TerminoGlosario(termino='Mesosistema',
            definicion='Relaciones entre distintos microsistemas en el modelo de Bronfenbrenner. En esta plataforma: la articulación entre el grupo académico del estudiante (carrera, cohorte) y los recursos institucionales de la UAA disponibles desde el ecosistema.'),
        TerminoGlosario(termino='ARIA',
            definicion='Accessible Rich Internet Applications. Conjunto de atributos HTML que permiten añadir semántica de accesibilidad a elementos dinámicos de las interfaces web, facilitando la interacción con tecnologías asistivas como lectores de pantalla.'),
    ]
    db.session.add_all(terminos)

    # ── MÓDULO DE EJEMPLO ─────────────────────────────────────────────────
    print("Creando módulo de ejemplo...")

    modulo = Modulo(
        titulo='Introducción al Ecosistema Digital Educativo Inclusivo',
        descripcion='Módulo introductorio que presenta los fundamentos teóricos del ecosistema: DUA, WCAG 2.2 y perspectiva ecológica de Bronfenbrenner.',
        activo=True
    )
    db.session.add(modulo)
    db.session.flush()

    secciones = [
        SeccionModulo(modulo_id=modulo.id, orden=1, titulo='¿Qué es un ecosistema digital educativo inclusivo?', icono='📖',
            contenido_texto="""<p>Un <strong>Ecosistema Digital Educativo Inclusivo</strong> es un conjunto articulado de actores, tecnologías, prácticas pedagógicas, políticas institucionales y contextos socioculturales que interactúan de manera dinámica e interdependiente para configurar una experiencia educativa accesible, equitativa y personalizada para la diversidad de los estudiantes en la educación superior.</p>

<p>A diferencia de las adaptaciones reactivas e individuales que agregan ajustes a posteriori, el modelo de ecosistema se fundamenta en un cambio paradigmático: diseñar la arquitectura pedagógica y tecnológica del entorno digital anticipando la diversidad funcional, sensorial, cognitiva y cultural desde el origen.</p>

<blockquote cite="CAST (2024). Universal Design for Learning Guidelines version 3.0. Wakefield, MA: Author.">
  <p>El propósito del Diseño Universal para el Aprendizaje no es simplemente eliminar barreras físicas o digitales, sino proporcionar entornos de aprendizaje flexibles y sistemáticamente diseñados que empoderen a todos los aprendices para convertirse en aprendices expertos, estratégicos y motivados.</p>
</blockquote>

<p>Para hacer operativa esta visión en las instituciones de educación superior, la plataforma integra tres pilares conceptuales interconectados:</p>

<ul>
  <li><strong>Diseño Universal para el Aprendizaje (DUA)</strong>: Marco pedagógico que propone ofrecer múltiples formas de representación de la información, múltiples formas de acción y expresión del conocimiento, y múltiples formas de implicación y motivación.</li>
  <li><strong>Web Content Accessibility Guidelines (WCAG 2.2)</strong>: Estándar técnico internacional desarrollado por el W3C que establece los criterios de accesibilidad web organizados bajo los cuatro <strong>Principios POUR</strong>: Perceptible, Operable, Comprensible y Robusto.</li>
  <li><strong>Modelo Ecológico del Desarrollo Humano</strong>: Perspectiva sistémica adaptada de Urie Bronfenbrenner que analiza las interacciones del estudiante con la tecnología a través de diferentes niveles de complejidad e influencia contextual.</li>
</ul>

<p>La perspectiva ecológica permite comprender la experiencia digital universitaria como un sistema dinámico estructurado en cuatro niveles de interacción:</p>

<ol>
  <li><strong>Microsistema</strong>: El entorno inmediato de interacción directa, representado por la interfaz de la plataforma web, las preferencias de accesibilidad elegidas por el usuario y los recursos pedagógicos interactivos.</li>
  <li><strong>Mesosistema</strong>: Las relaciones y flujos de comunicación entre los entornos del estudiante, como la vinculación entre el grupo académico de la carrera, los docentes y las herramientas institucionales de la UAA.</li>
  <li><strong>Exosistema</strong>: Las condiciones e infraestructuras indirectas que influyen en el proceso educativo, tales como las políticas institucionales de accesibilidad digital y las decisiones de diseño del plan de estudios.</li>
  <li><strong>Macrosistema</strong>: El marco sociocultural, legal y ético que promueve la inclusión educativa y los derechos digitales en la educación superior mexicana.</li>
</ol>

<p>En este marco, la plena compatibilidad con las <strong>Tecnologías Asistivas</strong> (como lectores de pantalla, programas de magnificación y dispositivos de entrada alternativos) se consolida como una garantía técnica indispensable para el ejercicio del derecho a una educación inclusiva y equitativa de calidad.</p>"""),
        SeccionModulo(modulo_id=modulo.id, orden=2, titulo='Los tres pilares del modelo', icono='🏛️',
            contenido_texto='El modelo propuesto se fundamenta en tres pilares que se articulan de manera coherente: DUA v3.0 (pilar pedagógico), WCAG 2.2 nivel AA (pilar técnico) y la teoría ecológica de Bronfenbrenner adaptada al contexto digital (pilar sistémico).'),
        SeccionModulo(modulo_id=modulo.id, orden=3, titulo='DUA: Diseño Universal para el Aprendizaje', icono='🎓',
            contenido_texto='El DUA propone diseñar los entornos educativos anticipando la diversidad desde el origen. Sus tres principios — representación múltiple, acción y expresión diversa, e implicación activa — guían el diseño pedagógico de este ecosistema.'),
        SeccionModulo(modulo_id=modulo.id, orden=4, titulo='WCAG 2.2 en la práctica', icono='♿',
            contenido_texto='Las WCAG 2.2 establecen los criterios técnicos de accesibilidad web organizados en cuatro principios POUR. El nivel AA es el estándar requerido por la mayoría de las normativas internacionales de accesibilidad.'),
        SeccionModulo(modulo_id=modulo.id, orden=5, titulo='Perspectiva ecológica de Bronfenbrenner', icono='🌐',
            contenido_texto='El modelo de Bronfenbrenner organiza los contextos de desarrollo en sistemas concéntricos: microsistema (entorno inmediato), mesosistema (relaciones entre microsistemas), exosistema (contextos indirectos) y macrosistema (dimensiones culturales y normativas).'),
        SeccionModulo(modulo_id=modulo.id, orden=6, titulo='Evaluación formativa', icono='✏️',
            contenido_texto='Demuestra tu comprensión de los conceptos a través de una de las tres modalidades de respuesta disponibles: selección múltiple, texto libre o selección visual.'),
    ]
    db.session.add_all(secciones)

    # ── ACTIVIDAD DE EJEMPLO ──────────────────────────────────────────────
    actividad = Actividad(
        modulo_id=modulo.id,
        titulo='Los principios POUR de WCAG 2.2',
        pregunta='¿Cuál de los siguientes enunciados describe correctamente los cuatro principios POUR de las WCAG 2.2?',
        tipo='seleccion',
        opciones_json=json.dumps([
            {'id': 'a', 'texto': 'Perceptible, Operable, Comprensible y Robusto'},
            {'id': 'b', 'texto': 'Perceptible, Observable, Comprensible y Robusto'},
            {'id': 'c', 'texto': 'Presentable, Operable, Comprensible y Robusto'},
            {'id': 'd', 'texto': 'Perceptible, Operable, Claro y Robusto'},
        ]),
        respuesta_correcta='a',
        retroalimentacion='¡Correcto! POUR: Perceptible (el contenido debe poder percibirse), Operable (los componentes deben poder operarse), Comprensible (la información debe ser comprensible) y Robusto (compatible con tecnologías asistivas actuales y futuras). Estos cuatro principios son la base de toda la estructura de WCAG 2.2.'
    )
    db.session.add(actividad)

    # ── GUARDAR TODO ──────────────────────────────────────────────────────
    db.session.commit()

    print()
    print("=" * 60)
    print("  DATOS DE PRUEBA CARGADOS CORRECTAMENTE")
    print("=" * 60)
    print()
    print("  Cuentas de demostración (contraseña: la de DEMO_PASSWORD):")
    print("    admin@demo.example    (Administrador)")
    print("    docente@demo.example  (Docente)")
    print("    alumno@demo.example   (Estudiante, preferencia por audio)")
    print("    roberto@demo.example  (Estudiante, alto contraste)")
    print("    maria@demo.example    (Estudiante, densidad reducida y sin audio)")
    print("    luis@demo.example     (Estudiante, texto muy grande)")
    print("    sofia@demo.example    (Estudiante, texto y recursos visuales)")
    print()
    print("  Grupos creados: 4")
    print("  Términos de glosario: 7")
    print("  Módulo: 1 (con 6 secciones y 1 actividad)")
    print()
    print("  Ahora ejecuta: python run.py (o docker compose up --build)")
    print("=" * 60)
