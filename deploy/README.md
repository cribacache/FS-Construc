# Migración a un VPS (Ubuntu 24.04)

Resultado: el sitio corre en un solo servidor con nginx + gunicorn + PostgreSQL local, fotos en disco
y respaldos diarios. Los scripts no se han ejecutado todavía en un servidor real: haz la primera
pasada con calma y revisa la salida de cada paso.

**Necesitas:** un VPS con Ubuntu 24.04 (2 GB de RAM alcanzan; Django 6 pide Python 3.12+, que trae
24.04), acceso SSH por llave, y `gcloud` autenticado en tu computador.

## 1. Antes (con un día de anticipación)
Baja el TTL del DNS para que el cambio de IP propague rápido:
```bash
for h in fsconstrucciones.cl. www.fsconstrucciones.cl.; do
  gcloud dns record-sets update $h --zone=fsconstrucciones-cl --type=A --ttl=60 \
    --rrdatas=136.68.32.45 --project=fs-construcciones
done
```

## 2. Sacar los datos de Google Cloud (en tu computador)
```bash
bash deploy/export_from_gcp.sh      # solo lee; deja todo en ./migration-export/ (ignorado por git)
scp -r migration-export root@IP_DEL_VPS:/root/
```

## 3. Preparar el VPS (como root)
```bash
git clone https://github.com/cribacache/FS-Construc.git /root/fs && cd /root/fs
bash deploy/setup.sh fsconstrucciones.cl tu@correo.cl
```
`certbot` va a fallar mientras el DNS apunte a Google: es normal, se repite en el paso 6.
Al final imprime la ruta secreta del admin (queda en `/etc/fsconstrucciones.env`).

## 4. Cargar los datos
```bash
bash deploy/restore.sh /root/migration-export/db.sql.gz /root/migration-export/media
```
Reemplaza la base y copia las fotos. Los errores por el rol `cloudsqlsuperuser` son esperables.
Si empiezas de cero en vez de restaurar: `createsuperuser` e `import_gallery` (ver salida de setup.sh).

## 5. Probar antes de cambiar el DNS
```bash
curl -I --resolve fsconstrucciones.cl:80:IP_DEL_VPS http://fsconstrucciones.cl/
```
(o agrega la IP a tu `/etc/hosts`). Revisa fotos, formulario de contacto y el login de `/mis-fotos/`.

## 6. Cambiar el DNS y activar HTTPS
```bash
for h in fsconstrucciones.cl. www.fsconstrucciones.cl.; do
  gcloud dns record-sets update $h --zone=fsconstrucciones-cl --type=A --ttl=300 \
    --rrdatas=IP_DEL_VPS --project=fs-construcciones
done
# en el VPS, cuando el dominio ya resuelva a él:
certbot --nginx -d fsconstrucciones.cl -d www.fsconstrucciones.cl --agree-tos -m tu@correo.cl --redirect
```
Hay un corte de ~1 minuto entre el cambio de DNS y el certificado. Después sube HSTS de a poco
editando `DJANGO_HSTS_SECONDS` en `/etc/fsconstrucciones.env` (300, luego 86400, luego 31536000) y
`systemctl restart fsconstrucciones`.

## 7. Respaldos
`backup.sh` corre a diario (3:15) y guarda 14 días en `/var/backups/fsconstrucciones`. **Eso no
protege si se pierde el VPS**: define `OFFSITE_TARGET=usuario@otro-servidor:/ruta/` en
`/etc/fsconstrucciones.env` para copiarlos a otro lugar. Para restaurar uno: `restore.sh db-FECHA.sql.gz`
(y `tar -xzf media-FECHA.tar.gz -C /srv/fsconstrucciones/media`).

## 8. Apagar Google Cloud (días después, ya verificado el VPS)
La zona DNS vive en el proyecto `fs-construcciones`: **no borres el proyecto entero** o el dominio deja
de resolver (los nameservers en NIC apuntan a Google). Borra solo los recursos que cuestan, dejando
la zona (centavos al mes). Es irreversible; guarda antes el export del paso 2.
```bash
P="--project=fs-construcciones"
gcloud compute forwarding-rules delete fs-construcciones-http-fr fs-construcciones-https-fr --global $P
gcloud compute target-https-proxies delete fs-construcciones-https-proxy $P
gcloud compute target-http-proxies delete fs-construcciones-http-proxy $P
gcloud compute url-maps delete fs-construcciones-urlmap fs-construcciones-urlmap-http $P
gcloud compute ssl-certificates delete fs-construcciones-cert --global $P
gcloud compute backend-services delete fs-construcciones-backend --global $P
gcloud compute network-endpoint-groups delete fs-construcciones-neg --region=southamerica-west1 $P
gcloud compute addresses delete fs-construcciones-ip --global $P
gcloud run services delete fs-construcciones --region=southamerica-west1 $P
gcloud sql instances delete fs-construcciones-db $P
gcloud storage rm -r gs://fs-construcciones-media
```

## Día a día
- Publicar cambios: `git push` y en el VPS `bash /srv/fsconstrucciones/app/deploy/update.sh`
- Logs: `journalctl -u fsconstrucciones -f` y `/var/log/nginx/error.log`
- Estado: `systemctl status fsconstrucciones nginx postgresql`
- Seguridad: entra solo por llave SSH (`PasswordAuthentication no` en `/etc/ssh/sshd_config.d/`),
  PostgreSQL escucha solo en local, `ufw status` debe mostrar solo SSH, 80 y 443.
