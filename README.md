# Ecosistema Digital Educativo Inclusivo — UAA

**Prototipo Sprint 0 — Plataforma Web Accesible bajo Principios DUA y WCAG 2.2 Nivel AA**  
*Doctorado en Ciencias Aplicadas de la Computación / Universidad Autónoma de Aguascalientes*

---

## 📌 Descripción del Proyecto

Este prototipo corresponde al desarrollo del **Ecosistema Digital Educativo Inclusivo**, una plataforma web diseñada para garantizar el acceso equitativo al aprendizaje universitario mediante:

1. **Diseño Universal para el Aprendizaje (DUA):** Múltiples formas de representación, expresión y motivación sin estigmatizar a los usuarios con diagnósticos médicos.
2. **Pautas de Accesibilidad Web (WCAG 2.2 Nivel AA):** Estructura semántica estricta (`landmarks`, jerarquía de encabezados sin saltos, ARIA live regions, controles accesibles por teclado, soporte de zoom al 200% y alto contraste).
3. **Gestión Académica Multinivel:** Soporte para tres roles diferenciados (Administrador, Docente y Estudiante).

---

## 🛠️ Tecnologías y Arquitectura

- **Lenguaje:** Python 3.10+
- **Framework Web:** Flask 3.1.3
- **ORM / Base de Datos:** SQLAlchemy 2.0 / Flask-SQLAlchemy 3.1 (SQLite en entorno local, compatible con PostgreSQL)
- **Autenticación y Seguridad:** Flask-Login 0.6.3, Werkzeug Security (hashing seguro de contraseñas), Flask-WTF con protección CSRF
- **Frontend:** HTML5 Semántico, Jinja2, CSS3 puro (arquitectura CSS modular accesible, sin dependencias externas pesadas)

---

## 📂 Estructura del Proyecto

```text
ecosistema/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css          # Estilos CSS accesibles (variables, temas, alto contraste)
│   │   └── js/
│   │       └── accesibilidad.js  # Lógica cliente (preferencias, glosario, anuncios)
│   ├── templates/                # Plantillas Jinja2 semánticas
│   │   ├── base.html             # Layout principal accesible con landmarks y skip links
│   │   ├── inicio.html           # Página de bienvenida
│   │   ├── login.html            # Acceso de usuarios
│   │   ├── registro.html         # Registro de estudiantes con configuración DUA inicial
│   │   ├── modulo.html           # Visor de contenidos pedagógicos accesibles
│   │   ├── actividad.html        # Evaluaciones y actividades interactivas
│   │   ├── perfil.html           # Ajustes de perfil y preferencias del estudiante
│   │   ├── accesibilidad.html    # Panel de personalización sensorial y DUA
│   │   ├── panel_admin.html      # Gestión de usuarios, grupos y analítica global
│   │   └── panel_docente.html    # Seguimiento de estudiantes y progreso por grupo
│   ├── __init__.py               # Application Factory de Flask
│   ├── forms.py                  # Formularios Flask-WTF con validaciones
│   ├── models.py                 # Modelos relacionales (Usuario, Grupo, Módulo, Actividad, etc.)
│   ├── routes.py                 # Rutas y controladores de la aplicación
│   ├── ruta_docente.py           # Ruta docente: cursos, diagnóstico y resultado
│   ├── diagnostico.py            # Instrumento de diagnóstico y su puntuación (sin Flask)
│   ├── planeacion.py             # Catálogo de decisiones DUA por unidad (sin Flask)
│   └── plan_export.py            # Exportación del plan a Word y Markdown
├── instance/                     # Base de datos SQLite local (generada automáticamente)
├── requirements.txt              # Dependencias del proyecto
├── requirements-dev.txt          # Dependencias de pruebas
├── tests/                        # Pruebas automáticas (seguridad y datos de prueba)
├── Dockerfile                    # Imagen para ejecutar con Docker
├── docker-compose.yml            # Ejecución local con un comando
├── run.py                        # Punto de entrada para ejecución local
├── seed.py                       # Datos de prueba (solo si la base está vacía)
├── render.yaml                   # Configuración para despliegue en la nube
└── .gitignore                    # Reglas de exclusión de Git
```

---

## 🚀 Cómo ejecutar el prototipo

Repositorio: <https://github.com/carevalomx69/EcosistemaDigitalnclusivoUAA>

### Opción A. Con Docker (recomendada para revisar avances)

Requiere Docker Desktop (o Docker Engine con Compose).

```bash
git clone https://github.com/carevalomx69/EcosistemaDigitalnclusivoUAA.git
cd EcosistemaDigitalnclusivoUAA
docker compose up --build
```

Abre <http://localhost:8000>. La base de datos se guarda en un volumen de Docker,
así que los datos sobreviven a reinicios. Para empezar de cero:
`docker compose down -v`.

### Opción B. Con Python

Requiere Python 3.10 o superior.

En **Windows (PowerShell)**:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python run.py
```

En **Linux / macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
python run.py
```

Abre <http://127.0.0.1:5000>.

`seed.py` solo carga los datos de prueba si la base está vacía. Para borrar todo y
volver a sembrar: `python seed.py --reset`.

### Pruebas automáticas

```bash
pip install -r requirements-dev.txt
python -m pytest
```

---

## 🧭 Ruta docente (en desarrollo)

Recorrido guiado en cinco pasos para quien quiere iniciar con enseñanza inclusiva:
1. Diagnóstico del curso (disponible)
2. Planeación con DUA (disponible): unidades del curso, 8 decisiones por unidad ligadas al diagnóstico y plan descargable en Word (.docx) o texto (.md)
3. Creación o adaptación con criterios WCAG 2.2
4. Verificación
5. Cierre y resumen

El diagnóstico es una autoevaluación orientativa de 14 afirmaciones organizadas por los tres
principios del DUA. No es un instrumento validado; se afinará con el piloto. La ruta guarda datos
del curso y respuestas del diagnóstico, nunca datos de estudiantes.

## 🔑 Cuentas de demostración

Son cuentas ficticias. **Todas usan la contraseña de la variable de entorno
`DEMO_PASSWORD`.** Si no se define y se ejecuta en local, la contraseña es
`demo-local-2026`. No hay contraseñas fijas en el servidor desplegado.

| Rol | Correo | Perfil de preferencias |
| :--- | :--- | :--- |
| Administrador | `admin@demo.example` | Panel de control global |
| Docente | `docente@demo.example` | Grupos y seguimiento, y la ruta docente (pasos 1 y 2) |
| Estudiante | `alumno@demo.example` | Prefiere audio y ritmo lento |
| Estudiante | `roberto@demo.example` | Texto grande y alto contraste |
| Estudiante | `maria@demo.example` | Densidad reducida, sin audio |
| Estudiante | `luis@demo.example` | Texto muy grande, interfaz de baja densidad |
| Estudiante | `sofia@demo.example` | Texto y recursos visuales |

---

## ☁️ Despliegue en Render

El archivo `render.yaml` describe el servicio. Pasos, una sola vez:

1. En Render: **New > Blueprint** y elige este repositorio.
2. Render crea el servicio y genera `SECRET_KEY` y `DEMO_PASSWORD`.
3. La contraseña de las cuentas de demostración se consulta en el servicio, en
   **Environment**, variable `DEMO_PASSWORD`.
4. Cada cambio que llegue a la rama `main` se despliega automáticamente.

Notas del plan gratuito: el servicio se apaga tras un rato sin uso y tarda cerca de
un minuto en despertar, y el disco es efímero (la base se reinicia en cada arranque).
Para una demostración conviene abrir la página unos minutos antes.

---

## 🔒 Seguridad y privacidad

- `SECRET_KEY` es obligatoria cuando `APP_ENV=production`; sin ella la aplicación no arranca.
- Todos los formularios que envían datos (POST) exigen token CSRF.
- El parámetro `next` del login solo acepta rutas internas.
- Cookies de sesión `HttpOnly`, `SameSite=Lax` y `Secure` en producción (requiere HTTPS).
- Cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y, en producción, HSTS.
- El repositorio no contiene contraseñas ni datos de personas reales.
- Antes de pilotear con personas reales: aviso de privacidad y consentimiento informado.

---

## ♿ Características Clave de Accesibilidad Implementadas

- **Navegación por Teclado:** Enlace directo de salto (*Skip to content*) y foco visible consistente en todos los elementos interactivos.
- **Jerarquía Semántica:** Estructura de encabezados `<h1>` a `<h6>` estricta, landmarks HTML5 (`<main>`, `<nav>`, `<aside>`, `<header>`, `<footer>`).
- **Compatibilidad con Lectores de Pantalla:** Atributos ARIA (`aria-live`, `aria-expanded`, `aria-describedby`, `role="progressbar"` completo).
- **Adaptación Visual Dinámica:** Controles para tamaño de fuente (Normal, Grande, Muy Grande), modos de contraste (Normal, Alto Contraste) y densidad de lectura.
- **Soporte DUA de Contenidos:** Módulos de aprendizaje con glosario contextual, lectura en voz alta (*Text-to-Speech*) y retroalimentación formativa inmediata en actividades.
