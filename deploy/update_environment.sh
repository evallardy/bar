#!/bin/bash
set -euo pipefail

# Uso:
#   sudo bash deploy/update_environment.sh <ambiente> <proyecto>
# Ejemplo:
#   sudo bash deploy/update_environment.sh desarrollo bar

if [ "$#" -ne 2 ]; then
    echo "Uso: $0 <desarrollo|calidad|produccion> <proyecto>"
    exit 1
fi

ambiente="$1"
proyecto="$2"

case "$ambiente" in
    desarrollo)
        prefijo="des"
        ruta_base="/home/desa"
        ;;
    calidad)
        prefijo=""
        ruta_base="/home/iagevm"
        ;;
    produccion)
        prefijo=""
        ruta_base="/home/produccion"
        ;;
    *)
        echo "El ambiente debe ser desarrollo, calidad o produccion."
        exit 1
        ;;
esac

service_name="${prefijo}${proyecto}"
app_dir="${ruta_base}/${proyecto}"
venv_dir="${app_dir}/.venv"
env_file="${app_dir}/deploy/.env.deploy"

if [ ! -d "$app_dir" ]; then
    echo "No existe la carpeta ${app_dir}."
    echo "Primero ejecuta deploy/setup_environment.sh para crear la instalacion inicial."
    exit 1
fi

if [ ! -f "$env_file" ]; then
    echo "No existe el archivo de entorno ${env_file}."
    echo "Crea la instalacion inicial con deploy/setup_environment.sh o restaura ese archivo."
    exit 1
fi

if grep -q "cambia-esta-" "$env_file"; then
    echo "${env_file} aun contiene placeholders."
    echo "Edita BAR_SECRET_KEY y BAR_DB_PASSWORD antes de actualizar."
    exit 2
fi

echo "=== Actualizando ${service_name} desde GitHub ==="
cd "$app_dir"
git fetch origin
git pull --ff-only origin main

echo "=== Activando entorno virtual ==="
. "$venv_dir/bin/activate"
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "=== Cargando variables de entorno ==="
set -a
. "$env_file"
set +a

echo "=== Ejecutando pasos Django ==="
python manage.py migrate --settings=bar.settings_prod
python manage.py collectstatic --noinput --settings=bar.settings_prod
python manage.py check --settings=bar.settings_prod

echo "=== Reiniciando servicios ==="
sudo supervisorctl restart "$service_name"
sudo nginx -t
sudo systemctl reload nginx
sudo supervisorctl status "$service_name"

deactivate

echo "Actualizacion terminada para ${service_name}."