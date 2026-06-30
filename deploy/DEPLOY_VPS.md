# Deploy en VPS Linux

Este flujo asume por defecto:

- dominio: `bar.iagmexico.com`
- app en `/srv/bar/app`
- entorno en `/etc/bar/bar.env`
- Nginx + Supervisor + Gunicorn

Si tu servidor usa otras rutas, cambia solo estas variables en `/etc/bar/bar.env` y en `deploy/supervisor/bar.conf`:

- `BAR_PROJECT_DIR`
- `BAR_VENV_DIR`
- `BAR_ENV_FILE`
- `BAR_GUNICORN_BIND`

## 1. Paquetes del servidor

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx supervisor mysql-client certbot python3-certbot-nginx
```

## 2. DNS

Apunta el registro `A` de `bar.iagmexico.com` a la IP pública del VPS.

## 3. Código y entorno virtual

```bash
sudo mkdir -p /srv/bar /etc/bar /var/log/bar /var/www/certbot
sudo chown -R $USER:www-data /srv/bar /var/log/bar /var/www/certbot
git clone <tu-repo> /srv/bar/app
cd /srv/bar/app
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Variables de entorno

```bash
sudo cp deploy/env/bar.env.example /etc/bar/bar.env
sudo chmod 640 /etc/bar/bar.env
sudo chown root:www-data /etc/bar/bar.env
sudo nano /etc/bar/bar.env
```

Ajusta al menos estas rutas si no usas la estructura por defecto:

```bash
BAR_PROJECT_DIR=/ruta/a/tu/proyecto
BAR_VENV_DIR=/ruta/a/tu/proyecto/.venv
BAR_ENV_FILE=/etc/bar/bar.env
```

## 5. Preparar Django

```bash
cd /srv/bar/app
. .venv/bin/activate
python manage.py migrate --settings=<modulo_proyecto>.settings_prod
python manage.py collectstatic --noinput --settings=<modulo_proyecto>.settings_prod
python manage.py bootstrap_bar --settings=<modulo_proyecto>.settings_prod
python manage.py check --settings=<modulo_proyecto>.settings_prod
```

## 6. Supervisor

```bash
sudo cp deploy/supervisor/bar.conf /etc/supervisor/conf.d/bar.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart bar
sudo supervisorctl status bar
```

## 7. Nginx HTTP inicial

Primero usa la configuración HTTP simple para poder validar conectividad si todavía no emites certificado.

```bash
sudo cp deploy/nginx/bar.conf /etc/nginx/sites-available/bar.conf
sudo ln -sf /etc/nginx/sites-available/bar.conf /etc/nginx/sites-enabled/bar.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 8. HTTPS con Certbot

Puedes usar la plantilla ya preparada o dejar que Certbot modifique Nginx.

Opción con plantilla HTTPS incluida:

```bash
sudo cp deploy/nginx/bar-ssl.conf /etc/nginx/sites-available/bar.conf
sudo nginx -t
sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/www/certbot -d bar.iagmexico.com
sudo nginx -t
sudo systemctl reload nginx
```

Opción automática con Certbot y Nginx:

```bash
sudo certbot --nginx -d bar.iagmexico.com
```

## 9. Actualización del proyecto

```bash
cd /srv/bar/app
git pull origin main
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --settings=<modulo_proyecto>.settings_prod
python manage.py collectstatic --noinput --settings=<modulo_proyecto>.settings_prod
python manage.py check --settings=<modulo_proyecto>.settings_prod
sudo supervisorctl restart bar
sudo systemctl reload nginx
```

## 9.1 Automatización con shell

El repositorio incluye [deploy/crea_proyecto.sh](deploy/crea_proyecto.sh) para crear una instalación nueva usando el flujo portable del proyecto.

Ejemplo:

```bash
sudo bash deploy/crea_proyecto.sh desarrollo bar bar-dev.iagmexico.com
```

La convención de rutas de los shells es:

- desarrollo: `/home/desarrollo/<proyecto>`
- calidad: `/home/calidad/<proyecto>`
- produccion: `/home/produccion/<proyecto>`

En los tres ambientes el servicio de Supervisor y el sitio de Nginx usan el mismo nombre base del proyecto, por ejemplo `bar`.

Qué hace:

- clona el repo en la ruta del ambiente
- crea `.venv` e instala dependencias
- crea `deploy/.env.deploy` con los valores base del proyecto
- recibe el dominio completo del sitio, sin asumir un sufijo fijo
- genera `migracion.sh`, `collectstatic.sh`, `restart.sh` y `status.sh` en la raíz del proyecto
- usa `deploy/gunicorn.sh` como comando directo de Supervisor y desde ahi arranca Gunicorn con `<modulo_proyecto>.settings_prod`
- toma como base las plantillas [deploy/supervisor/bar.conf](deploy/supervisor/bar.conf) y [deploy/nginx/bar.conf](deploy/nginx/bar.conf)
- en Nginx genera un upstream con el patron `<proyecto>conn` apuntando al socket de Gunicorn
- despliega los `.conf` finales en `/etc/supervisor/conf.d/` y `/etc/nginx/sites-available/`

Si el script se detiene avisando placeholders, edita `deploy/.env.deploy` y vuelve a ejecutarlo.

Para actualizaciones posteriores del mismo ambiente, usa [deploy/upd_environment.sh](deploy/upd_environment.sh):

```bash
sudo bash deploy/upd_environment.sh desarrollo bar
```

Qué hace:

- entra a la instalación existente del ambiente
- ejecuta `git pull --ff-only origin main`
- actualiza dependencias del virtualenv
- carga `deploy/.env.deploy`
- ejecuta `migrate`, `collectstatic` y `check` con el modulo Django del proyecto
- vuelve a desplegar Supervisor y Nginx desde las plantillas del repo
- reinicia Supervisor y recarga Nginx

## 10. Comandos útiles

```bash
sudo supervisorctl status bar
sudo supervisorctl restart bar
sudo tail -f /var/log/bar/gunicorn-error.log
sudo tail -f /var/log/bar/supervisor-err.log
sudo nginx -t
sudo systemctl status nginx
sudo certbot renew --dry-run
```
