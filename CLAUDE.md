# Notas para quien trabaje en este repositorio (personas y asistentes de IA)

Prototipo Flask del Ecosistema Digital Educativo Inclusivo (UAA). Puede ejecutarse en la raíz
(local, Render) o detrás de un Nginx compartido bajo la subruta `/ecosistema/` (Oracle Cloud).
Reglas que no deben romperse:

## 1. Rutas bajo una subruta
- En plantillas, usar siempre `url_for(...)`. Nunca `href="/..."`, `src="/..."` ni `action="/..."`.
- En JavaScript, no usar `fetch('/ruta')`. Leer la URL desde una etiqueta `<meta>` generada con
  `url_for` (ejemplo: `url-preferencias` en `base.html`).
- Con `TRUST_PROXY=1` la app lee `X-Forwarded-Prefix` (ProxyFix). Activarlo solo si el contenedor
  no publica puertos al exterior.
- `tests/test_subruta.py` vigila estas reglas. Probar también abriendo la app bajo `/ecosistema/`.

## 2. Cookies, HTTPS y variables
- En producción las cookies son `Secure` y se envía HSTS. Por HTTP plano (piloto sin dominio)
  hay que definir `COOKIE_SECURE=0`; si no, el inicio de sesión falla sin mensaje claro.
- `SECRET_KEY` y `DEMO_PASSWORD` van en `.env` del servidor. Nunca en el repositorio.

## 3. Despliegue en Oracle (servidor compartido con otras apps)
- No editar archivos a mano en el servidor. Todo cambio pasa por rama, pull request y merge.
- Orden: respaldo de la base, `git pull`, `docker compose -f docker-compose.oracle.yml up -d --build`, prueba.
- Nunca `docker compose down -v` (borra la base). No hacer `down` en la carpeta de las listas ligadas:
  cae el Nginx de todas las apps.
- Antes de cambiar `docker/nginx.conf` de las listas, copiar el archivo a `~/respaldos/`.
- No subir respaldos `.sql`, llaves SSH, contraseñas ni archivos `.env`.
- Guía completa: `docs/DESPLIEGUE_ORACLE.md`.

## 4. Datos y privacidad
- La ruta docente guarda datos del curso y respuestas del diagnóstico, nunca datos de estudiantes.
- Antes de un piloto con personas reales: aviso de privacidad aprobado y consentimiento informado.

## 5. Pruebas
- `pip install -r requirements-dev.txt && python -m pytest` debe pasar antes de cada merge.
