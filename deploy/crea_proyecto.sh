#!/bin/bash
set -euo pipefail

current_step="inicio"

log_step() {
    current_step="$1"
    echo "=== ${current_step} ==="
}

on_error() {
    local exit_code=$?
    local line_no=$1
    echo ""
    echo "[ERROR] El despliegue fallo en el paso: ${current_step}"
    echo "[ERROR] Linea: ${line_no}"
    echo "[ERROR] Comando: ${BASH_COMMAND}"
    echo "[ERROR] Codigo de salida: ${exit_code}"
    exit "$exit_code"
}

on_exit() {
    local exit_code=$?
    if [ "$exit_code" -eq 0 ]; then
        echo ""
        echo "[OK] Despliegue completado correctamente para ${service_name:-proyecto}."
    fi
}

trap 'on_error ${LINENO}' ERR
trap on_exit EXIT

# Uso:
#   sudo bash deploy/crea_proyecto.sh <ambiente> <proyecto> <dominio>
# Ejemplo:
#   sudo bash deploy/crea_proyecto.sh desarrollo bar bar-dev.iagmexico.com

if [ "$#" -ne 3 ]; then
    echo "Uso: $0 <desarrollo|calidad|produccion> <proyecto> <dominio>"
    exit 1
fi

ambiente="$1"
proyecto="$2"
dominio_entrada="$3"
django_module="${DJANGO_PROJECT_MODULE:-$proyecto}"
settings_module="${DJANGO_SETTINGS_MODULE_OVERRIDE:-${django_module}.settings_prod}"

github_owner="${GITHUB_OWNER:-evallardy}"
repo_url="https://github.com/${github_owner}/${proyecto}.git"

write_env_var() {
    local key="$1"
    local value="$2"
    printf '%s=%q\n' "$key" "$value" >> "$env_file"
}

escape_sed_replacement() {
    printf '%s' "$1" | sed -e 's/[&|]/\\&/g'
}

render_template() {
    local template_path="$1"
    local output_path="$2"

    if [ ! -f "$template_path" ]; then
        echo "No existe la plantilla ${template_path}."
        exit 1
    fi

    sed \
        -e "s|__SERVICE_NAME__|$(escape_sed_replacement "$service_name")|g" \
        -e "s|__SERVICE_USER__|$(escape_sed_replacement "$service_user")|g" \
        -e "s|__APP_DIR__|$(escape_sed_replacement "$app_dir")|g" \
        -e "s|__VENV_DIR__|$(escape_sed_replacement "$venv_dir")|g" \
        -e "s|__ENV_FILE__|$(escape_sed_replacement "$env_file")|g" \
        -e "s|__LOGS_DIR__|$(escape_sed_replacement "$logs_dir")|g" \
        -e "s|__SERVER_NAMES__|$(escape_sed_replacement "$server_names")|g" \
        -e "s|__GUNICORN_SOCKET__|$(escape_sed_replacement "$gunicorn_socket")|g" \
        "$template_path" > "$output_path"
}

case "$ambiente" in
    desarrollo)
        ruta_base="/home/desarrollo"
        service_user="${BAR_SERVICE_USER:-www-data}"
        ;;
    calidad)
        ruta_base="/home/calidad"
        service_user="${BAR_SERVICE_USER:-www-data}"
        ;;
    produccion)
        ruta_base="/home/produccion"
        service_user="${BAR_SERVICE_USER:-www-data}"
        ;;
    *)
        echo "El ambiente debe ser desarrollo, calidad o produccion."
        exit 1
        ;;
esac

service_name="${proyecto}"
if [[ "$dominio_entrada" == www.* ]]; then
    dominio_www="$dominio_entrada"
    dominio_fqdn="${dominio_entrada#www.}"
else
    dominio_fqdn="$dominio_entrada"
    dominio_www="www.${dominio_entrada}"
fi

server_names="$dominio_fqdn"
allowed_hosts="$dominio_fqdn"
csrf_trusted_origins="https://${dominio_fqdn}"

if [ "$dominio_www" != "$dominio_fqdn" ]; then
    server_names="${server_names} ${dominio_www}"
    allowed_hosts="${allowed_hosts},${dominio_www}"
    csrf_trusted_origins="${csrf_trusted_origins},https://${dominio_www}"
fi

app_dir="${ruta_base}/${proyecto}"
venv_dir="${app_dir}/.venv"
deploy_dir="${app_dir}/deploy"
env_file="${deploy_dir}/.env.deploy"
logs_dir="${app_dir}/logs"
migration_script="${app_dir}/migracion.sh"
collectstatic_script="${app_dir}/collectstatic.sh"
restart_script="${app_dir}/restart.sh"
status_script="${app_dir}/status.sh"
nginx_available="/etc/nginx/sites-available/${service_name}.conf"
nginx_enabled="/etc/nginx/sites-enabled/${service_name}.conf"
supervisor_conf="/etc/supervisor/conf.d/${service_name}.conf"
supervisor_template="${deploy_dir}/supervisor/bar.conf"
nginx_template="${deploy_dir}/nginx/bar.conf"
gunicorn_socket="/run/gunicorn-${service_name}.sock"

first_install=false

if [ ! -d "$app_dir" ]; then
    first_install=true
fi

log_step "Preparando estructura para ${service_name}"
mkdir -p "$ruta_base"

if [ "$first_install" = true ]; then
    sudo rm -f "$supervisor_conf" "$nginx_enabled" "$nginx_available"
    cd "$ruta_base"

    log_step "Clonando repositorio ${repo_url}"
    git clone "$repo_url" "$app_dir"
else
    echo "La carpeta ${app_dir} ya existe. Se reutilizara para completar o rehacer la configuracion."
fi

mkdir -p "$logs_dir"
touch "$logs_dir/err.log" "$logs_dir/out.log" "$logs_dir/nginx-access.log" "$logs_dir/nginx-error.log"
chmod 664 "$logs_dir/err.log" "$logs_dir/out.log" "$logs_dir/nginx-access.log" "$logs_dir/nginx-error.log"

log_step "Creando o reutilizando entorno virtual"
cd "$app_dir"
if [ ! -d "$venv_dir" ]; then
    python3 -m venv "$venv_dir"
fi
. "$venv_dir/bin/activate"
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

log_step "Preparando archivo de entorno"
if [ ! -f "$env_file" ]; then
    : > "$env_file"
    cat >> "$env_file" <<'EOF'
############################################################
### INICIO VARIABLES OBLIGATORIAS PARA EDITAR A MANO     ###
############################################################
# Cambia estos valores antes de volver a ejecutar el shell.
# Si dejas los placeholders, el despliegue se detendra.
EOF
    write_env_var "DJANGO_SETTINGS_MODULE" "$settings_module"
    write_env_var "BAR_PROJECT_DIR" "$app_dir"
    write_env_var "BAR_VENV_DIR" "$venv_dir"
    write_env_var "BAR_ENV_FILE" "$env_file"
    write_env_var "BAR_GUNICORN_APP" "${django_module}.wsgi:application"
    write_env_var "BAR_SECRET_KEY" "${BAR_SECRET_KEY:-cambia-esta-clave-por-una-larga-y-unica}"
    write_env_var "BAR_DB_ENGINE" "${BAR_DB_ENGINE:-django.db.backends.mysql}"
    write_env_var "BAR_DB_NAME" "${BAR_DB_NAME:-bar_db}"
    write_env_var "BAR_DB_USER" "${BAR_DB_USER:-bar_user}"
    write_env_var "BAR_DB_PASSWORD" "${BAR_DB_PASSWORD:-cambia-esta-password}"
    write_env_var "BAR_DB_HOST" "${BAR_DB_HOST:-127.0.0.1}"
    write_env_var "BAR_DB_PORT" "${BAR_DB_PORT:-3306}"
    cat >> "$env_file" <<'EOF'
############################################################
### FIN VARIABLES OBLIGATORIAS PARA EDITAR A MANO        ###
############################################################

############################################################
### INICIO VARIABLES GENERADAS AUTOMATICAMENTE           ###
############################################################
EOF
    write_env_var "BAR_ALLOWED_HOSTS" "$allowed_hosts"
    write_env_var "BAR_CSRF_TRUSTED_ORIGINS" "$csrf_trusted_origins"
    write_env_var "BAR_EMAIL_BACKEND" "${BAR_EMAIL_BACKEND:-django.core.mail.backends.smtp.EmailBackend}"
    write_env_var "BAR_EMAIL_HOST" "${BAR_EMAIL_HOST:-sandbox.smtp.mailtrap.io}"
    write_env_var "BAR_EMAIL_HOST_USER" "${BAR_EMAIL_HOST_USER:-}"
    write_env_var "BAR_EMAIL_HOST_PASSWORD" "${BAR_EMAIL_HOST_PASSWORD:-}"
    write_env_var "BAR_EMAIL_PORT" "${BAR_EMAIL_PORT:-2525}"
    write_env_var "BAR_EMAIL_USE_TLS" "${BAR_EMAIL_USE_TLS:-True}"
    write_env_var "BAR_GUNICORN_BIND" "unix:${gunicorn_socket}"
    write_env_var "BAR_GUNICORN_WORKERS" "${BAR_GUNICORN_WORKERS:-3}"
    write_env_var "BAR_GUNICORN_WORKER_CLASS" "${BAR_GUNICORN_WORKER_CLASS:-sync}"
    write_env_var "BAR_GUNICORN_TIMEOUT" "${BAR_GUNICORN_TIMEOUT:-120}"
    write_env_var "BAR_GUNICORN_GRACEFUL_TIMEOUT" "${BAR_GUNICORN_GRACEFUL_TIMEOUT:-30}"
    write_env_var "BAR_GUNICORN_KEEPALIVE" "${BAR_GUNICORN_KEEPALIVE:-5}"
    write_env_var "BAR_GUNICORN_ACCESSLOG" "${logs_dir}/gunicorn-access.log"
    write_env_var "BAR_GUNICORN_ERRORLOG" "${logs_dir}/gunicorn-error.log"
    write_env_var "BAR_SESSION_COOKIE_SECURE" "${BAR_SESSION_COOKIE_SECURE:-True}"
    write_env_var "BAR_CSRF_COOKIE_SECURE" "${BAR_CSRF_COOKIE_SECURE:-True}"
    write_env_var "BAR_SECURE_SSL_REDIRECT" "${BAR_SECURE_SSL_REDIRECT:-True}"
    write_env_var "BAR_SECURE_HSTS_SECONDS" "${BAR_SECURE_HSTS_SECONDS:-31536000}"
    write_env_var "BAR_SECURE_HSTS_INCLUDE_SUBDOMAINS" "${BAR_SECURE_HSTS_INCLUDE_SUBDOMAINS:-True}"
    write_env_var "BAR_SECURE_HSTS_PRELOAD" "${BAR_SECURE_HSTS_PRELOAD:-True}"
    cat >> "$env_file" <<'EOF'
############################################################
### FIN VARIABLES GENERADAS AUTOMATICAMENTE              ###
############################################################
EOF
    chmod 600 "$env_file"
fi

log_step "Generando script de migracion"
cat > "$migration_script" <<EOF
#!/bin/bash
set -euo pipefail

PROJECT_DIR="\$(cd -- "\$(dirname -- "\${BASH_SOURCE[0]}")" && pwd)"

cd "\$PROJECT_DIR"
. "\$PROJECT_DIR/.venv/bin/activate"
set -a
. "\$PROJECT_DIR/deploy/.env.deploy"
set +a
python manage.py migrate --settings="${settings_module}"
EOF
chmod +x "$migration_script"

log_step "Generando script de collectstatic"
cat > "$collectstatic_script" <<EOF
#!/bin/bash
set -euo pipefail

PROJECT_DIR="\$(cd -- "\$(dirname -- "\${BASH_SOURCE[0]}")" && pwd)"

cd "\$PROJECT_DIR"
. "\$PROJECT_DIR/.venv/bin/activate"
set -a
. "\$PROJECT_DIR/deploy/.env.deploy"
set +a
python manage.py collectstatic --noinput --settings="${settings_module}"
EOF
chmod +x "$collectstatic_script"

log_step "Generando script de reinicio"
cat > "$restart_script" <<EOF
#!/bin/bash
set -euo pipefail

SERVICE_NAME="${service_name}"

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart "\$SERVICE_NAME"
sudo nginx -t
sudo systemctl reload nginx
sudo supervisorctl status "\$SERVICE_NAME"
EOF
chmod +x "$restart_script"

log_step "Generando script de estado"
cat > "$status_script" <<EOF
#!/bin/bash
set -euo pipefail

SERVICE_NAME="${service_name}"
GUNICORN_SOCKET="${gunicorn_socket}"
LOGS_DIR="${logs_dir}"

echo "=== Supervisor ==="
sudo supervisorctl status "\$SERVICE_NAME"
echo ""
echo "=== Nginx ==="
sudo nginx -t
echo ""
echo "=== Socket Gunicorn ==="
if [ -S "\$GUNICORN_SOCKET" ]; then
    ls -l "\$GUNICORN_SOCKET"
else
    echo "No existe el socket \$GUNICORN_SOCKET"
fi
echo ""
echo "=== Ultimas lineas Gunicorn ==="
tail -n 20 "\$LOGS_DIR/gunicorn-error.log" || true
EOF
chmod +x "$status_script"

if grep -q "cambia-esta-" "$env_file"; then
    echo "Se creo ${env_file} con placeholders."
    echo "Busca el bloque 'INICIO VARIABLES OBLIGATORIAS PARA EDITAR A MANO'."
    echo "Edita BAR_SECRET_KEY y BAR_DB_PASSWORD, luego vuelve a ejecutar el mismo comando."
    exit 2
fi

set -a
. "$env_file"
set +a

log_step "Ejecutando migraciones y validaciones"
python manage.py migrate --settings="$settings_module"
python manage.py collectstatic --noinput --settings="$settings_module"
python manage.py check --settings="$settings_module"

log_step "Desplegando configuracion de Supervisor desde plantilla"
render_template "$supervisor_template" "$supervisor_conf"

chmod +x "${app_dir}/deploy/gunicorn_start.sh"

log_step "Desplegando configuracion de Nginx desde plantilla"
render_template "$nginx_template" "$nginx_available"

ln -sf "$nginx_available" "$nginx_enabled"

log_step "Recargando servicios"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart "$service_name"
sudo nginx -t
sudo systemctl reload nginx
sudo supervisorctl status "$service_name"

deactivate

echo "Archivo de entorno: ${env_file}"
echo "Repositorio: ${repo_url}"