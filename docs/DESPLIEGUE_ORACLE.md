# Despliegue en Oracle Cloud bajo /ecosistema/

Resultado esperado: `http://140.84.191.7/ecosistema/` atendido por el Nginx del puerto 80
(contenedor `listas_nginx`), igual que `/simulador/`.

> Los bloques de Nginx de abajo son una propuesta. Hay que ajustarlos al `docker/nginx.conf`
> real del servidor, que no está en git.

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

## 2. Bloques de Nginx (en el `server` del puerto 80)
Con variable y resolver de Docker, Nginx arranca aunque este contenedor no exista. Así una falla
de esta app no tira las demás.
```nginx
    location = /ecosistema { return 301 /ecosistema/; }

    location /ecosistema/ {
        resolver 127.0.0.11 valid=10s;
        set $ecosistema http://ecosistema_web:8000;
        rewrite ^/ecosistema/(.*)$ /$1 break;
        proxy_pass $ecosistema;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Prefix /ecosistema;
    }
```
Aplicar y verificar:
```bash
docker exec listas_nginx nginx -t        # debe decir "syntax is ok" antes de recargar
docker exec listas_nginx nginx -s reload
curl -I http://localhost/simulador/      # sigue en 200
curl -I http://localhost/ecosistema/     # 200 o 302 a /ecosistema/login
```
Si el `nginx.conf` está dentro de la imagen (como en las listas), reconstruir solo ese servicio:
`docker compose build webserver && docker compose up -d --no-deps webserver`.

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
Retirar la app sin afectar a las demás: quitar los bloques de Nginx, recargar y `docker stop ecosistema_web`.
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
