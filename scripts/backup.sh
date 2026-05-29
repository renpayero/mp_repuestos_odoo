#!/usr/bin/env bash
# Backup de MPRepuestos: dump lógico de la base (pg_dump -Fc) + filestore.
# Pensado para correr desde cron en el host.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${HERE}/../docker/docker-compose.yml"
COMPOSE="docker compose -p mprepuestos -f ${COMPOSE_FILE}"

# Cargar .env para DB_NAME / POSTGRES_USER
ENV_FILE="${HERE}/../docker/.env"
[ -f "${ENV_FILE}" ] && { set -a; . "${ENV_FILE}"; set +a; }
DB="${DB_NAME:-mprepuestos}"
PUSER="${POSTGRES_USER:-odoo}"

DEST="${BACKUP_DIR:-/opt/mprepuestos/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "${DEST}"

echo "[backup] pg_dump de '${DB}'..."
${COMPOSE} exec -T db pg_dump -U "${PUSER}" -Fc "${DB}" > "${DEST}/${DB}_${TS}.dump"

echo "[backup] filestore (/var/lib/odoo)..."
${COMPOSE} exec -T odoo tar czf - -C /var/lib/odoo . > "${DEST}/filestore_${TS}.tar.gz"

echo "[backup] retención > ${RETENTION_DAYS} días..."
find "${DEST}" -name '*.dump' -mtime +"${RETENTION_DAYS}" -delete
find "${DEST}" -name 'filestore_*.tar.gz' -mtime +"${RETENTION_DAYS}" -delete

echo "[backup] OK → ${DEST}/${DB}_${TS}.dump"
# TODO: sincronizar a almacenamiento externo / otra región (p.ej. rclone copy "${DEST}" remote:mprepuestos-backups)
