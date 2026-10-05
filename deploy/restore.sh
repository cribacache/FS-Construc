#!/usr/bin/env bash
# Restaura la base de datos (y opcionalmente las fotos) en el VPS. REEMPLAZA la base actual.
# Uso (como root): bash restore.sh db.sql.gz [carpeta-con-las-fotos]
#   Sirve tanto para el export de Google Cloud como para un respaldo hecho por backup.sh.
set -euo pipefail

DUMP="${1:?Uso: bash restore.sh <db.sql|db.sql.gz> [carpeta_fotos]}"
MEDIA_SRC="${2:-}"

APP_USER=fsapp
BASE=/srv/fsconstrucciones
APP_DIR=$BASE/app
VENV=$BASE/venv
MEDIA_DIR=$BASE/media
ENV_FILE=/etc/fsconstrucciones.env

[ "$(id -u)" -eq 0 ] || { echo "Ejecuta como root"; exit 1; }
[ -f "$DUMP" ] || { echo "No existe $DUMP"; exit 1; }
DUMP="$(realpath "$DUMP")"
[ -z "$MEDIA_SRC" ] || MEDIA_SRC="$(realpath "$MEDIA_SRC")"
# fsapp/postgres no pueden leer la carpeta actual; sudo -u la hereda.
cd /

echo "Esto BORRA la base 'fsconstrucciones' actual y la reemplaza por $DUMP."
read -r -p "Escribe SI para continuar: " answer
[ "$answer" = "SI" ] || { echo "Cancelado."; exit 1; }

manage() {
  sudo -u "$APP_USER" bash -c "set -a; . '$ENV_FILE'; set +a; cd '$APP_DIR' && '$VENV/bin/python' manage.py $*"
}

systemctl stop fsconstrucciones
sudo -u postgres dropdb --if-exists fsconstrucciones
sudo -u postgres createdb -O "$APP_USER" fsconstrucciones

# Se carga como fsapp (no como postgres) para que todo quede a su nombre. Los errores por el
# rol "cloudsqlsuperuser" del export de Google Cloud son esperables y no afectan los datos.
errlog="$(mktemp)"
if [[ "$DUMP" == *.gz ]]; then
  gunzip -c "$DUMP" | sudo -u "$APP_USER" psql -q -d fsconstrucciones 2> "$errlog" || true
else
  sudo -u "$APP_USER" psql -q -d fsconstrucciones -f "$DUMP" 2> "$errlog" || true
fi
echo "Errores de psql: $(grep -c 'ERROR' "$errlog" || true) (detalle en $errlog)"
grep 'ERROR' "$errlog" | grep -vi 'cloudsqlsuperuser' | head -5 || true

if [ -n "$MEDIA_SRC" ]; then
  rsync -a "$MEDIA_SRC"/ "$MEDIA_DIR"/
  chown -R "$APP_USER":"$APP_USER" "$MEDIA_DIR"
  find "$MEDIA_DIR" -type d -exec chmod 755 {} +
  find "$MEDIA_DIR" -type f -exec chmod 644 {} +
fi

manage migrate --noinput
systemctl start fsconstrucciones

echo "Filas restauradas:"
sudo -u "$APP_USER" psql -d fsconstrucciones -tAc \
  "SELECT 'fotos=' || (SELECT count(*) FROM website_galleryimage) || '  mensajes=' || (SELECT count(*) FROM website_contactmessage) || '  usuarios=' || (SELECT count(*) FROM auth_user)"
echo "Las sesiones anteriores quedan invalidas (clave nueva): hay que volver a iniciar sesion."
