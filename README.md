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
│   │       └── main.js           # Lógica cliente (preferencias DUA, glosario, TTS)
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
│   └── routes.py                 # Rutas y controladores de la aplicación
├── instance/                     # Base de datos SQLite local (generada automáticamente)
├── requirements.txt              # Dependencias del proyecto
├── run.py                        # Punto de entrada para ejecución local
├── seed.py                       # Población de base de datos con datos de prueba
├── render.yaml                   # Configuración para despliegue en la nube
└── .gitignore                    # Reglas de exclusión de Git
```

---

## 🚀 Guía de Instalación y Ejecución Local

### 1. Clonar o descargar el repositorio
```bash
git clone https://github.com/Magdy-10/ecosistema-inclusivo-uaa.git
cd ecosistema-inclusivo-uaa
```

### 2. Crear y activar el entorno virtual

En **Windows (PowerShell / CMD)**:
```bash
python -m venv venv
venv\Scripts\activate
```

En **Linux / macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Inicializar y poblar la base de datos de prueba
Ejecuta el script `seed.py` para crear las tablas relacionales y cargar los datos de prueba (grupos, usuarios, módulos pedagógicos y actividades):
```bash
python seed.py
```

### 5. Iniciar el servidor local
```bash
python run.py
```

Abre tu navegador en:  
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Credenciales de Prueba (Seed Data)

El script `seed.py` preconfigura cuentas representativas para validar las funcionalidades y los diferentes perfiles DUA:

| Rol | Correo Electrónico | Contraseña | Perfil / Caso de Uso |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@uaa.mx` | `admin2025` | Panel de control global, gestión de cuentas y carreras. |
| **Docente** | `docente@uaa.mx` | `docente2025` | Gestión de grupos, seguimiento de progreso y analíticas. |
| **Estudiante** (Visual / Audio) | `alumno@uaa.mx` | `alumno2025` | Preferencia por audio/multimodal (baja visión / preferencia auditiva). |
| **Estudiante** (Alto Contraste) | `roberto@uaa.mx` | `alumno2025` | Texto grande, contraste reforzado. |
| **Estudiante** (Auditivo / Texto) | `maria@uaa.mx` | `alumno2025` | Densidad reducida, formatos prioritarios en texto y visual. |
| **Estudiante** (Neurodivergencia) | `luis@uaa.mx` | `alumno2025` | Texto muy grande, interfaz limpia de baja densidad cognitiva (TDAH). |
| **Estudiante** (General) | `sofia@uaa.mx` | `alumno2025` | Modalidad estándar texto y recursos visuales. |

---

## ♿ Características Clave de Accesibilidad Implementadas

- **Navegación por Teclado:** Enlace directo de salto (*Skip to content*) y foco visible consistente en todos los elementos interactivos.
- **Jerarquía Semántica:** Estructura de encabezados `<h1>` a `<h6>` estricta, landmarks HTML5 (`<main>`, `<nav>`, `<aside>`, `<header>`, `<footer>`).
- **Compatibilidad con Lectores de Pantalla:** Atributos ARIA (`aria-live`, `aria-expanded`, `aria-describedby`, `role="progressbar"` completo).
- **Adaptación Visual Dinámica:** Controles para tamaño de fuente (Normal, Grande, Muy Grande), modos de contraste (Normal, Alto Contraste) y densidad de lectura.
- **Soporte DUA de Contenidos:** Módulos de aprendizaje con glosario contextual, lectura en voz alta (*Text-to-Speech*) y retroalimentación formativa inmediata en actividades.
