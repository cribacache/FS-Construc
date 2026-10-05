#!/usr/bin/env bash
# Corre en TU computador (con gcloud autenticado). Baja de Google Cloud la base de datos y
# las fotos a ./migration-export/ para llevarlas al VPS. Solo LEE: no borra ni cambia nada
# del sitio en produccion. El dump va a un bucket temporal PRIVADO que se elimina al terminar
# (nunca al bucket de fotos, que es publico).
set -euo pipefail

PROJECT=fs-construcciones
INSTANCE=fs-construcciones-db
DB=fsconstrucciones
MEDIA_BUCKET=fs-construcciones-media
TMP_BUCKET="$PROJECT-migration-$(date +%s)"
OUT=./migration-export

cleanup() { gcloud storage rm -r "gs://$TMP_BUCKET" --project="$PROJECT" >/dev/null 2>&1 || true; }
trap cleanup EXIT

mkdir -p "$OUT/media"

echo "==> Bucket temporal privado"
gcloud storage buckets create "gs://$TMP_BUCKET" --project="$PROJECT" \
  --location=southamerica-west1 --uniform-bucket-level-access --public-access-prevention

sql_sa="$(gcloud sql instances describe "$INSTANCE" --project="$PROJECT" --format='value(serviceAccountEmailAddress)')"
gcloud storage buckets add-iam-policy-binding "gs://$TMP_BUCKET" \
  --member="serviceAccount:$sql_sa" --role=roles/storage.objectAdmin >/dev/null

echo "==> Exportando la base de datos"
gcloud sql export sql "$INSTANCE" "gs://$TMP_BUCKET/db.sql.gz" --database="$DB" --project="$PROJECT"
gcloud storage cp "gs://$TMP_BUCKET/db.sql.gz" "$OUT/db.sql.gz"

echo "==> Copiando las fotos"
gcloud storage cp -r "gs://$MEDIA_BUCKET/*" "$OUT/media/"

echo
echo "Listo en $OUT/ (contiene mensajes de contacto y hashes de contrasenas: no lo subas a git)."
echo "Archivos de fotos: $(find "$OUT/media" -type f | wc -l | tr -d ' ')"
