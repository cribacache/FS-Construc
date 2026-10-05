#!/usr/bin/env bash
# Publica la ultima version de main en el VPS. Uso (como root): bash update.sh
set -euo pipefail

APP_USER=fsapp
BASE=/srv/fsconstrucciones
APP_DIR=$BASE/app
VENV=$BASE/venv
ENV_FILE=/etc/fsconstrucciones.env

[ "$(id -u)" -eq 0 ] || { echo "Ejecuta como root"; exit 1; }
cd /

manage() {
  sudo -u "$APP_USER" bash -c "set -a; . '$ENV_FILE'; set +a; cd '$APP_DIR' && '$VENV/bin/python' manage.py $*"
}

sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
sudo -u "$APP_USER" "$VENV/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
manage collectstatic --noinput
manage migrate --noinput
systemctl restart fsconstrucciones
echo "Actualizado a $(git -C "$APP_DIR" rev-parse --short HEAD)"
