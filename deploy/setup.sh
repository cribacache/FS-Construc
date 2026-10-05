#!/usr/bin/env bash
# Prepara un VPS Ubuntu 24.04 limpio para correr FS Construcciones.
# Uso (como root):  bash setup.sh fsconstrucciones.cl [correo-para-certbot]
# Es seguro volver a ejecutarlo: no pisa el archivo de entorno ni la base existente.
set -euo pipefail

DOMAIN="${1:?Uso: bash setup.sh dominio.cl [correo-para-certbot]}"
EMAIL="${2:-}"
REPO_URL="${REPO_URL:-https://github.com/cribacache/FS-Construc.git}"
BRANCH="${BRANCH:-main}"

APP_USER=fsapp
BASE=/srv/fsconstrucciones
APP_DIR=$BASE/app
VENV=$BASE/venv
MEDIA_DIR=$BASE/media
BACKUP_DIR=/var/backups/fsconstrucciones
ENV_FILE=/etc/fsconstrucciones.env

[ "$(id -u)" -eq 0 ] || { echo "Ejecuta como root (sudo bash setup.sh ...)"; exit 1; }
# fsapp no puede leer la carpeta actual (ej. /root); sudo -u la hereda y git/python fallan.
cd /

echo "==> Paquetes del sistema"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv git nginx postgresql certbot python3-certbot-nginx \
  ufw fail2ban unattended-upgrades rsync curl

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' \
  || { echo "Django 6 necesita Python 3.12 o mas. Reinstala el VPS con Ubuntu 24.04."; exit 1; }

echo "==> Usuario y carpetas"
id "$APP_USER" >/dev/null 2>&1 \
  || useradd --system --create-home --home-dir "$BASE" --shell /usr/sbin/nologin "$APP_USER"
# 711: nginx (www-data) puede entrar a /media y /static, pero nadie lista la carpeta.
chmod 711 "$BASE"
install -d -o "$APP_USER" -g "$APP_USER" -m 755 "$MEDIA_DIR"
install -d -o "$APP_USER" -g "$APP_USER" -m 700 "$BACKUP_DIR"

echo "==> Codigo"
if [ ! -d "$APP_DIR/.git" ]; then
  sudo -u "$APP_USER" git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
else
  sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
fi
[ -d "$VENV" ] || sudo -u "$APP_USER" python3 -m venv "$VENV"
sudo -u "$APP_USER" "$VENV/bin/pip" install --quiet --upgrade pip
sudo -u "$APP_USER" "$VENV/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

echo "==> PostgreSQL (solo local, autenticacion por socket)"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$APP_USER'" | grep -q 1 \
  || sudo -u postgres createuser "$APP_USER"
sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='fsconstrucciones'" | grep -q 1 \
  || sudo -u postgres createdb -O "$APP_USER" fsconstrucciones

echo "==> Variables de entorno"
if [ ! -f "$ENV_FILE" ]; then
  secret_key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(60))')"
  admin_url="staff-$(python3 -c 'import secrets; print(secrets.token_hex(6))')/"
  ( umask 077
    sed -e "s|__DOMAIN__|$DOMAIN|g" -e "s|__SECRET_KEY__|$secret_key|" -e "s|__ADMIN_URL__|$admin_url|" \
      "$APP_DIR/deploy/env.example" > "$ENV_FILE" )
  chown root:"$APP_USER" "$ENV_FILE"
  chmod 640 "$ENV_FILE"
else
  echo "    $ENV_FILE ya existe, no se toca."
fi

manage() {
  sudo -u "$APP_USER" bash -c "set -a; . '$ENV_FILE'; set +a; cd '$APP_DIR' && '$VENV/bin/python' manage.py $*"
}

echo "==> Django: estaticos, migraciones y tabla de cache"
manage collectstatic --noinput
manage migrate --noinput
manage createcachetable

echo "==> Servicio gunicorn"
install -m 644 "$APP_DIR/deploy/gunicorn.service" /etc/systemd/system/fsconstrucciones.service
systemctl daemon-reload
systemctl enable --now fsconstrucciones
systemctl restart fsconstrucciones

echo "==> nginx"
sed "s|__DOMAIN__|$DOMAIN|g" "$APP_DIR/deploy/nginx-fsconstrucciones.conf" \
  > /etc/nginx/sites-available/fsconstrucciones
ln -sf /etc/nginx/sites-available/fsconstrucciones /etc/nginx/sites-enabled/fsconstrucciones
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> Firewall y proteccion basica"
ssh_port="$(sshd -T 2>/dev/null | awk '/^port /{print $2; exit}')"
ufw allow "${ssh_port:-22}/tcp"
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
systemctl enable --now fail2ban
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> Backups diarios (3:15 AM)"
chmod +x "$APP_DIR"/deploy/*.sh
echo "15 3 * * * $APP_USER $APP_DIR/deploy/backup.sh >> $BACKUP_DIR/backup.log 2>&1" \
  > /etc/cron.d/fsconstrucciones-backup

echo "==> Certificado HTTPS"
if [ -n "$EMAIL" ]; then
  certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect \
    || echo "    certbot fallo (normal si el DNS todavia apunta a otro servidor). Repite despues del cambio de DNS:
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --agree-tos -m $EMAIL --redirect"
else
  echo "    Sin correo: omitido. Despues del cambio de DNS ejecuta:
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --agree-tos -m TU_CORREO --redirect"
fi

echo
echo "Listo. Ruta del admin (guardala): /$(grep '^DJANGO_ADMIN_URL=' "$ENV_FILE" | cut -d= -f2)"
echo "Siguiente paso: restaurar los datos (deploy/restore.sh) o, si empiezas de cero:"
echo "  sudo -u $APP_USER bash -c \"set -a; . $ENV_FILE; set +a; cd $APP_DIR && $VENV/bin/python manage.py createsuperuser\""
echo "  (y 'manage.py import_gallery' para cargar las fotos iniciales)"
echo "Recomendado: entra por SSH solo con llave y desactiva la contrasena (PasswordAuthentication no)."
