# Deploy en VPS Linux

Este flujo asume:

- dominio: `bar.iagmexico.com`
- app en `/srv/bar/app`
- entorno en `/etc/bar/bar.env`
- Nginx + Supervisor + Gunicorn

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

## 5. Preparar Django

```bash
cd /srv/bar/app
. .venv/bin/activate
python manage.py migrate --settings=bar.settings_prod
python manage.py collectstatic --noinput --settings=bar.settings_prod
python manage.py bootstrap_bar --settings=bar.settings_prod
python manage.py check --settings=bar.settings_prod
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
python manage.py migrate --settings=bar.settings_prod
python manage.py collectstatic --noinput --settings=bar.settings_prod
python manage.py check --settings=bar.settings_prod
sudo supervisorctl restart bar
sudo systemctl reload nginx
```

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
