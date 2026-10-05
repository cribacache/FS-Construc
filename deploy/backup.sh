#!/usr/bin/env bash
# Respaldo de la base de datos y las fotos. Lo ejecuta cron como el usuario fsapp.
# Para que sirva ante la perdida del VPS, define OFFSITE_TARGET (ej: usuario@otro-servidor:/ruta/)
# en /etc/fsconstrucciones.env: se copia ahi por rsync sobre SSH.
set -euo pipefail

ENV_FILE=/etc/fsconstrucciones.env
[ -r "$ENV_FILE" ] && { set -a; . "$ENV_FILE"; set +a; }

BACKUP_DIR="${BACKUP_DIR:-/var/backups/fsconstrucciones}"
MEDIA_DIR="${DJANGO_MEDIA_ROOT:-/srv/fsconstrucciones/media}"
DB_NAME="${DB_NAME:-fsconstrucciones}"
KEEP_DAYS="${KEEP_DAYS:-14}"

umask 077
mkdir -p "$BACKUP_DIR"
stamp="$(date +%Y%m%d-%H%M%S)"

pg_dump --no-owner --no-privileges "$DB_NAME" | gzip > "$BACKUP_DIR/db-$stamp.sql.gz"
tar -czf "$BACKUP_DIR/media-$stamp.tar.gz" -C "$MEDIA_DIR" .

find "$BACKUP_DIR" -type f \( -name 'db-*.sql.gz' -o -name 'media-*.tar.gz' \) -mtime +"$KEEP_DAYS" -delete

if [ -n "${OFFSITE_TARGET:-}" ]; then
  rsync -a "$BACKUP_DIR/" "$OFFSITE_TARGET"
fi
echo "$(date -Is) respaldo $stamp ok"
