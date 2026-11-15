# Despliegue en Oracle Cloud bajo /ecosistema/

Resultado esperado: `http://140.84.191.7/ecosistema/` atendido por el Nginx del puerto 80
(contenedor `listas_nginx`), igual que `/simulador/`.

> Los bloques de Nginx están ajustados al `docker/nginx.conf` real del servidor (noviembre de 2026),
> que no está en git.

## 0. Antes de empezar
1. Respaldos en `~/respaldos/`: copia de `docker/nginx.conf` y volcado de la base del simulador.
2. Confirmar que el simulador responde: `curl -I http://localhost/simulador/` debe dar 200.

## 1. Levantar el contenedor
```bash
cd ~ && git clone https://github.com/carevalomx69/EcosistemaDigitalnclusivoUAA.git
cd EcosistemaDigitalnclusivoUAA
cp .env.example .env && nano .env      # SECRET_KEY, DEMO_PASSWORD y datos del aviso
docker compose -f docker-compose.oracle.yml up -d --build
docker logs ecosistema_web --tail 20
```
La red `simuladorfinanciero_mi_red` debe existir (`docker network ls`). El contenedor no publica puertos.

## 2. Bloques de Nginx
El Nginx de las listas (`listas_nginx`) se construye desde `~/Estructuras_de_datos_UAA/docker/nginx.conf`
y el archivo va dentro de la imagen. Hay que copiarlo a `~/respaldos/`, editarlo y reconstruir el servicio.

Agregar estos bloques dentro del `server` existente, junto a los del simulador:
```nginx
    # ============================================================
    # Ecosistema Digital Inclusivo: sub-ruta /ecosistema/
    # A diferencia del simulador, el nombre del contenedor se resuelve en cada
    # petición (resolver de Docker + variable). Así, si ecosistema_web no existe
    # o está detenido, Nginx arranca igual y el simulador no se ve afectado.
    # ============================================================
    location = /ecosistema {
        return 301 /ecosistema/;
    }

    location ^~ /ecosistema/ {
        resolver 127.0.0.11 valid=10s;
        set $ecosistema_upstream http://ecosistema_web:8000;
        rewrite ^/ecosistema/(.*)$ /$1 break;
        proxy_pass $ecosistema_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /ecosistema;
    }
```
Si `ecosistema_web` está detenido, `/ecosistema/` responde 502 y todo lo demás sigue igual.

Orden y verificación (primero el contenedor, luego Nginx):
```bash
# 1. El contenedor de la app ya debe estar arriba (sección 1)
docker ps --filter name=ecosistema_web

# 2. Respaldo y edición
cd ~/Estructuras_de_datos_UAA
cp docker/nginx.conf ~/respaldos/nginx.conf.bak.$(date +%Y%m%d_%H%M)
nano docker/nginx.conf            # pegar los bloques dentro del server

# 3. Reconstruir y probar la sintaxis ANTES de reemplazar el Nginx en marcha
docker compose build webserver
docker run --rm --network simuladorfinanciero_mi_red estructuras_de_datos_uaa-webserver nginx -t

# 4. Solo si dice "syntax is ok" y "test is successful"
docker compose up -d --no-deps webserver

# 5. Comprobar
curl -I http://localhost/simulador/      # sigue en 200
curl -I http://localhost/ecosistema/     # 200, o 302 a /ecosistema/login
```
Si algo falla, volver a la configuración anterior con los pasos de `MANTENIMIENTO_2026-10.md`, sección 4.
No usar `docker compose down` en esa carpeta: cae el Nginx de todas las apps.
(El nombre de la imagen `estructuras_de_datos_uaa-webserver` sale de esa nota; verificarlo con `docker images`.)

## 3. Cuentas de docentes
Entrar como `admin@demo.example` (contraseña `DEMO_PASSWORD`) > Panel de administración > crear usuario con
rol Docente y contraseña temporal. No compartir la cuenta `docente@demo.example`.

## 4. Lista de verificación desde fuera de la red del servidor
- Inicio de sesión como docente y que la sesión persista al navegar.
- Ruta docente completa, pasos 1 a 5, y descarga del plan en Word.
- Cambiar tamaño de texto o contraste y recargar (prueba el guardado de preferencias bajo la subruta).
- Reiniciar el contenedor (`docker restart ecosistema_web`) y comprobar que el curso sigue ahí.

## 5. Actualizar y revertir
Actualizar: respaldo del volumen, `git pull`, `docker compose -f docker-compose.oracle.yml up -d --build`.
Retirar la app sin afectar a las demás: quitar los bloques de Nginx, reconstruir `webserver` como en la sección 2 y `docker stop ecosistema_web`.
Respaldo del volumen:
```bash
docker run --rm -v ecosistemadigitalnclusivouaa_ecosistema-data:/d -v ~/respaldos:/b alpine \
  tar czf /b/ecosistema_$(date +%Y%m%d_%H%M).tgz -C /d .
```
(el prefijo del volumen depende del nombre de la carpeta; verificar con `docker volume ls`).

## 6. Pendientes antes de ampliar el piloto
- Dominio con HTTPS y quitar `COOKIE_SECURE=0`.
- Respaldos programados y copiados fuera del servidor.
- Aviso de privacidad aprobado por la UAA.
