# Bar

[![Django CI](https://github.com/evallardy/bar/actions/workflows/django-ci.yml/badge.svg)](https://github.com/evallardy/bar/actions/workflows/django-ci.yml)

Sistema web para operar un bar o restaurante pequeño con flujo de comandas, producción por área, entregas, caja y administración básica. Está construido con Django y una sola aplicación principal llamada `core`.

## Qué resuelve

El proyecto centraliza la operación del turno en una interfaz web con módulos separados para:

- alta y seguimiento de comandas por mesa
- tablero de cocina para productos de comida
- tablero de bar para bebidas
- tablero de entregas para artículos listos por entregar
- caja con pagos parciales por producto y cierre de comandas
- administración de productos, insumos, variantes, recetas y usuarios
- apertura y cierre de día de trabajo

## Características principales

- Gestión de productos terminados con precio, categoría, descripción, estado y existencia.
- Gestión de insumos disponibles para recetas o composición de productos.
- Variantes por producto con inventario propio y ajuste de precio.
- Control de stock visible solo para productos o variantes disponibles al momento de comandar.
- Comandas por mesa con múltiples artículos, notas y nombre de comensal opcional.
- Separación operativa por áreas: cocina, bar, caja y entregas.
- Flujo de estados para artículos: comandado, en preparación, por entregar, entregado o cancelado.
- Cobro por artículo con mezcla de métodos de pago: efectivo, tarjeta y transferencia.
- Registro de evidencias para pagos con tarjeta y transferencia.
- Cierre de comandas solo cuando no quedan artículos pendientes de pago.
- Apertura y cierre de días de trabajo con trazabilidad de usuario responsable.
- Control de acceso por rol y permisos por módulo.

## Stack técnico

- Python 3
- Django 5.2.13
- MySQL como base de datos principal
- SQLite para pruebas mediante `bar.settings_test`
- PyMySQL y mysqlclient como conectores disponibles
- Plantillas Django para frontend
- Archivos estáticos propios en `static/`
- Archivos de media para evidencias de pago en `media/`

## Integración continua

El repositorio ejecuta automáticamente `python manage.py check --settings=bar.settings_test` y `python manage.py test --settings=bar.settings_test` en cada push y pull request hacia `main` mediante GitHub Actions.

## Estructura general

- `bar/`: configuración del proyecto Django.
- `core/`: lógica de negocio, modelos, formularios, vistas, servicios y pruebas.
- `templates/`: vistas HTML del sistema.
- `static/`: estilos del sitio.
- `media/`: evidencias de pagos subidas por usuarios.
- `manage.py`: entrada principal para tareas de Django.

## Módulos funcionales

### Inicio

Panel con métricas rápidas del turno y accesos a las áreas operativas.

### Administrador

Permite operar catálogo y configuración:

- productos
- insumos
- variantes
- recetas o insumos por producto
- ventas por día laboral
- apertura y cierre del día de trabajo

### Comandas

Permite crear y consultar comandas activas por mesa, agregar artículos y agrupar consumo por mesa.

### Cocina y Bar

Muestran tableros de producción separados según la categoría del producto:

- `COMIDA` va a cocina
- `BEBIDA` va a bar

### Entregas

Muestra artículos listos para entregar a la mesa.

### Caja

Permite revisar importes por comanda, registrar pagos parciales por artículo, consultar historial de pagos y cerrar comandas pagadas.

### Usuarios y permisos

Cada usuario tiene un perfil de acceso con rol y permisos independientes por módulo:

- menú
- administrador
- comanda
- cocina
- bar
- entregas
- caja

## Modelo de dominio resumido

Entidades principales:

- `Product`: producto vendible.
- `Supply`: insumo o ingrediente base.
- `ProductSupply`: relación entre producto e insumo.
- `ProductVariant`: variante con stock y delta de precio.
- `WorkDay`: día de trabajo abierto o cerrado.
- `Order`: comanda o mesa.
- `OrderItem`: artículo dentro de una comanda.
- `OrderPayment`: pago aplicado a una comanda.
- `OrderItemPayment`: relación entre pago y artículo cobrado.
- `UserAccess`: rol y permisos funcionales por usuario.

## Requisitos

- Python 3.10 o superior compatible con Django 5.2
- MySQL accesible en `127.0.0.1:3306` para desarrollo local con la configuración por defecto
- Variables de entorno para producción o para credenciales distintas a las locales

Variables soportadas por configuración:

- `BAR_DEBUG`
- `BAR_SECRET_KEY`
- `BAR_ALLOWED_HOSTS`
- `BAR_CSRF_TRUSTED_ORIGINS`
- `BAR_DB_ENGINE`
- `BAR_DB_NAME`
- `BAR_DB_USER`
- `BAR_DB_PASSWORD`
- `BAR_DB_HOST`
- `BAR_DB_PORT`
- `BAR_EMAIL_BACKEND`
- `BAR_EMAIL_HOST`
- `BAR_EMAIL_HOST_USER`
- `BAR_EMAIL_HOST_PASSWORD`
- `BAR_EMAIL_PORT`
- `BAR_EMAIL_USE_TLS`
- `BAR_RUNSERVER_ADDRPORT`
- `BAR_SESSION_COOKIE_SECURE`
- `BAR_CSRF_COOKIE_SECURE`
- `BAR_SECURE_SSL_REDIRECT`
- `BAR_SECURE_HSTS_SECONDS`
- `BAR_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `BAR_SECURE_HSTS_PRELOAD`

## Configuración de deploy

El proyecto ya incluye una configuración separada para producción en `bar.settings_prod`.

Qué hace `bar.settings_prod`:

- fuerza `DEBUG=False`
- exige `BAR_SECRET_KEY`
- exige hosts explícitos en `BAR_ALLOWED_HOSTS`
- habilita `SecurityMiddleware` y `WhiteNoiseMiddleware`
- sirve archivos estáticos desde `STATIC_ROOT`

Variables mínimas para producción:

- `DJANGO_SETTINGS_MODULE=bar.settings_prod`
- `BAR_SECRET_KEY`
- `BAR_ALLOWED_HOSTS`
- `BAR_CSRF_TRUSTED_ORIGINS`
- `BAR_DB_ENGINE`
- `BAR_DB_NAME`
- `BAR_DB_USER`
- `BAR_DB_PASSWORD`
- `BAR_DB_HOST`
- `BAR_DB_PORT`

Variables recomendadas para endurecer producción:

- `BAR_SESSION_COOKIE_SECURE=True`
- `BAR_CSRF_COOKIE_SECURE=True`
- `BAR_SECURE_SSL_REDIRECT=True`
- `BAR_SECURE_HSTS_SECONDS=31536000`
- `BAR_SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `BAR_SECURE_HSTS_PRELOAD=True`

Comandos típicos de despliegue:

```powershell
python manage.py migrate --settings=bar.settings_prod
python manage.py collectstatic --noinput --settings=bar.settings_prod
python manage.py bootstrap_bar --settings=bar.settings_prod
```

Si tu plataforma usa WSGI o ASGI sin indicar settings manualmente, `bar/wsgi.py` y `bar/asgi.py` ya apuntan por defecto a `bar.settings_prod`.

El archivo `Procfile` usa `gunicorn` y está pensado para despliegues Linux como Render, Railway o Heroku-like.

## Deploy con Nginx, Supervisor y Gunicorn

El repositorio ya incluye plantillas para ese stack en `deploy/`:

- `deploy/gunicorn.conf.py`
- `deploy/gunicorn_start.sh`
- `deploy/supervisor/bar.conf`
- `deploy/nginx/bar.conf`
- `deploy/nginx/bar-ssl.conf`
- `deploy/env/bar.env.example`
- `deploy/DEPLOY_VPS.md`

Suposiciones de estas plantillas:

- código del proyecto en `/srv/bar/app`
- archivo de entorno en `/etc/bar/bar.env`
- usuario del proceso web: `www-data`
- socket Unix de Gunicorn en `/run/gunicorn-bar.sock`
- logs en `/var/log/bar/`

Ejemplo de `/etc/bar/bar.env`:

```bash
DJANGO_SETTINGS_MODULE=bar.settings_prod
BAR_SECRET_KEY=cambia-esta-clave
BAR_ALLOWED_HOSTS=bar.iagmexico.com
BAR_CSRF_TRUSTED_ORIGINS=https://bar.iagmexico.com
BAR_DB_ENGINE=django.db.backends.mysql
BAR_DB_NAME=bar_db
BAR_DB_USER=bar_user
BAR_DB_PASSWORD=cambia-esta-password
BAR_DB_HOST=127.0.0.1
BAR_DB_PORT=3306
```

El mismo ejemplo ya está listo para copiar desde `deploy/env/bar.env.example`.

Pasos típicos en el servidor:

```bash
sudo mkdir -p /srv/bar /etc/bar /var/log/bar
sudo chown -R $USER:www-data /srv/bar
git clone <tu-repo> /srv/bar/app
cd /srv/bar/app
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example /etc/bar/bar.env
python manage.py migrate --settings=bar.settings_prod
python manage.py collectstatic --noinput --settings=bar.settings_prod
python manage.py bootstrap_bar --settings=bar.settings_prod
sudo cp deploy/supervisor/bar.conf /etc/supervisor/conf.d/bar.conf
sudo cp deploy/nginx/bar.conf /etc/nginx/sites-available/bar.conf
sudo ln -s /etc/nginx/sites-available/bar.conf /etc/nginx/sites-enabled/bar.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart bar
sudo nginx -t
sudo systemctl reload nginx
```

Para un flujo más completo con HTTPS y actualización del proyecto, revisa `deploy/DEPLOY_VPS.md`.

Ajustes que tienes que cambiar antes de usarlo:

- verificar que el path `/srv/bar/app` sea el real en los archivos de `deploy/`
- crear y proteger `/etc/bar/bar.env` con permisos restrictivos
- si vas a servir `media/` desde disco local, asegurar respaldo y persistencia

Dominio ya preparado en las plantillas:

- `bar.iagmexico.com` en `deploy/nginx/bar.conf`
- `bar.iagmexico.com` en `deploy/nginx/bar-ssl.conf`
- `bar.iagmexico.com` en el ejemplo de `BAR_ALLOWED_HOSTS`
- `https://bar.iagmexico.com` en el ejemplo de `BAR_CSRF_TRUSTED_ORIGINS`

HTTPS:

- `deploy/nginx/bar-ssl.conf` ya incluye redirección HTTP a HTTPS
- la ruta de certificados está preparada para `bar.iagmexico.com`
- puedes emitir el certificado con `certbot --nginx -d bar.iagmexico.com` o con `certonly --webroot`

Comandos de operación útiles:

```bash
sudo supervisorctl status bar
sudo supervisorctl restart bar
sudo tail -f /var/log/bar/gunicorn-error.log
sudo tail -f /var/log/bar/supervisor-err.log
sudo nginx -t
```

## Instalación local

1. Crear y activar un entorno virtual.
2. Instalar dependencias.
3. Crear la base de datos MySQL `bar_db`.
4. Ajustar credenciales si no coinciden con las de desarrollo.
5. Ejecutar migraciones.
6. Crear datos iniciales.
7. Levantar el servidor.

Ejemplo en Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py bootstrap_bar
python manage.py runserver
```

## Usuario inicial

El comando `bootstrap_bar` crea roles base y asegura un usuario administrador inicial en desarrollo.

Credenciales por defecto del bootstrap:

- usuario: `admin`
- contraseña: definida en el comando de bootstrap para ambiente local

Conviene cambiarlas después del primer acceso.

## Comandos útiles

```powershell
python manage.py migrate
python manage.py bootstrap_bar
python manage.py createsuperuser
python manage.py runserver
python manage.py test --settings=bar.settings_test
python manage.py check
```

Nota: `manage.py runserver` agrega por defecto `0.0.0.0:8000` si no se especifica una dirección explícita.

Si necesitas otro bind por defecto en desarrollo, puedes definir `BAR_RUNSERVER_ADDRPORT`, por ejemplo `127.0.0.1:9000`.

## Configuración de pruebas

El proyecto incluye `bar/settings_test.py`, que cambia la base de datos a SQLite y usa un hasher rápido para pruebas.

Ejemplo:

```powershell
python manage.py test --settings=bar.settings_test
```

## Flujo operativo esperado

1. Un administrador abre el día de trabajo.
2. El personal crea comandas por mesa.
3. Cocina y barra atienden artículos según su categoría.
4. El tablero de entregas concentra productos listos.
5. Caja registra pagos por artículo y por método.
6. La comanda se cierra cuando ya no existen pendientes de pago.
7. Al final del turno se cierra el día de trabajo.

## Consideraciones actuales

- La configuración principal lee variables de entorno y mantiene valores locales por defecto solo para desarrollo.
- Las evidencias de pago se almacenan en el sistema de archivos local bajo `media/`.
- El proyecto depende de que MySQL esté disponible para usar la configuración principal.

## Pendientes típicos para producción

- definir `BAR_DEBUG=False`
- definir `BAR_SECRET_KEY`
- restringir `BAR_ALLOWED_HOSTS`
- definir `BAR_CSRF_TRUSTED_ORIGINS`
- configurar servidor web y archivos estáticos
- configurar almacenamiento de media persistente
- endurecer credenciales iniciales y políticas de acceso
