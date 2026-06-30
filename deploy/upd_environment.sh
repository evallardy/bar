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
    echo "[ERROR] La actualizacion fallo en el paso: ${current_step}"
    echo "[ERROR] Linea: ${line_no}"
    echo "[ERROR] Comando: ${BASH_COMMAND}"
    echo "[ERROR] Codigo de salida: ${exit_code}"
    exit "$exit_code"
}

on_exit() {
    local exit_code=$?
    if [ "$exit_code" -eq 0 ]; then
        echo ""
        echo "[OK] Actualizacion completada correctamente para ${service_name:-proyecto}."
    fi
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
        -e "s|__UPSTREAM_NAME__|$(escape_sed_replacement "$upstream_name")|g" \
        -e "s|__GUNICORN_SOCKET__|$(escape_sed_replacement "$gunicorn_socket")|g" \
        "$template_path" > "$output_path"
}

resolve_service_user() {
    if [ -n "${BAR_SERVICE_USER:-}" ]; then
        printf '%s\n' "$BAR_SERVICE_USER"
        return
    fi

    local candidate=""

    if [ -d "$app_dir" ]; then
        candidate="$(stat -c '%U' "$app_dir" 2>/dev/null || true)"
    fi

    if [ -z "$candidate" ] || [ "$candidate" = "root" ]; then
        if [ -d "$ruta_base" ]; then
            candidate="$(stat -c '%U' "$ruta_base" 2>/dev/null || true)"
        fi
    fi

    if [ -z "$candidate" ] || [ "$candidate" = "root" ]; then
        candidate="${SUDO_USER:-${USER:-root}}"
    fi

    printf '%s\n' "$candidate"
}

trap 'on_error ${LINENO}' ERR
trap on_exit EXIT

# Uso:
#   sudo bash deploy/upd_environment.sh <ambiente> <proyecto>
# Ejemplo:
#   sudo bash deploy/upd_environment.sh desarrollo bar

if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <desarrollo|calidad|produccion> <proyecto>"
    exit 1
fi

ambiente="$1"
proyecto="$2"
django_module="${DJANGO_PROJECT_MODULE:-$proyecto}"
settings_module="${DJANGO_SETTINGS_MODULE_OVERRIDE:-${django_module}.settings_prod}"

case "$ambiente" in
    desarrollo)
        ruta_base="/home/desarrollo"
        ;;
    calidad)
        ruta_base="/home/calidad"
        ;;
    produccion)
        ruta_base="/home/produccion"
        ;;
    *)
        echo "El ambiente debe ser desarrollo, calidad o produccion."
        exit 1
        ;;
esac

service_name="${proyecto}"
upstream_name="${proyecto}conn"
app_dir="${ruta_base}/${proyecto}"
venv_dir="${app_dir}/.venv"
env_file="${app_dir}/deploy/.env.deploy"
deploy_dir="${app_dir}/deploy"
logs_dir="${app_dir}/logs"
supervisor_conf="/etc/supervisor/conf.d/${service_name}.conf"
nginx_available="/etc/nginx/sites-available/${service_name}.conf"
nginx_enabled="/etc/nginx/sites-enabled/${service_name}.conf"
supervisor_template="${deploy_dir}/supervisor/bar.conf"
nginx_template="${deploy_dir}/nginx/bar.conf"
service_user="$(resolve_service_user)"

if [ ! -d "$app_dir" ]; then
    echo "No existe la carpeta ${app_dir}."
    echo "Primero ejecuta deploy/crea_proyecto.sh para crear la instalacion inicial."
    exit 1
fi

if [ ! -f "$env_file" ]; then
    echo "No existe el archivo de entorno ${env_file}."
    echo "Crea la instalacion inicial con deploy/crea_proyecto.sh o restaura ese archivo."
    exit 1
fi

if grep -q "cambia-esta-" "$env_file"; then
    echo "${env_file} aun contiene placeholders."
    echo "Edita BAR_SECRET_KEY y BAR_DB_PASSWORD antes de actualizar."
    exit 2
fi

log_step "Actualizando ${service_name} desde GitHub"
cd "$app_dir"
git fetch origin
git pull --ff-only origin main

log_step "Activando entorno virtual"
. "$venv_dir/bin/activate"
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

log_step "Cargando variables de entorno"
set -a
. "$env_file"
set +a

gunicorn_socket="${BAR_GUNICORN_BIND#unix:}"
server_names="${BAR_ALLOWED_HOSTS//,/ }"

if [ -z "$server_names" ]; then
    echo "BAR_ALLOWED_HOSTS no esta definido en ${env_file}."
    exit 1
fi

log_step "Ejecutando pasos Django"
python manage.py migrate --settings="$settings_module"
python manage.py collectstatic --noinput --settings="$settings_module"
python manage.py check --settings="$settings_module"

chmod +x "${app_dir}/deploy/gunicorn_start.sh"
chmod +x "${app_dir}/deploy/gunicorn.sh"

log_step "Desplegando configuracion de Supervisor y Nginx desde plantillas"
render_template "$supervisor_template" "$supervisor_conf"
render_template "$nginx_template" "$nginx_available"
ln -sf "$nginx_available" "$nginx_enabled"

log_step "Reiniciando servicios"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart "$service_name"
sudo nginx -t
sudo systemctl reload nginx
sudo supervisorctl status "$service_name"

deactivate