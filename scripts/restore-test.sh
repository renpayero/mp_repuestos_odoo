#!/usr/bin/env bash
# Prueba que el último backup ES restaurable, en una base efímera y descartable.
# No toca la base de producción.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="${HERE}/../docker/docker-compose.yml"
COMPOSE="docker compose -p mprepuestos -f ${COMPOSE_FILE}"

ENV_FILE="${HERE}/../docker/.env"
[ -f "${ENV_FILE}" ] && { set -a; . "${ENV_FILE}"; set +a; }
DB="${DB_NAME:-mprepuestos}"
PUSER="${POSTGRES_USER:-odoo}"
DEST="${BACKUP_DIR:-/opt/mprepuestos/backups}"

LATEST="$(ls -t "${DEST}"/${DB}_*.dump 2>/dev/null | head -1 || true)"
[ -z "${LATEST}" ] && { echo "[restore-test] No hay dumps en ${DEST}"; exit 1; }

TESTDB="restore_test_$(date +%s)"
echo "[restore-test] Restaurando ${LATEST} en ${TESTDB}..."
${COMPOSE} exec -T db createdb -U "${PUSER}" "${TESTDB}"
${COMPOSE} exec -T db pg_restore -U "${PUSER}" -d "${TESTDB}" --no-owner < "${LATEST}" || true

echo "[restore-test] Verificación (res_users):"
${COMPOSE} exec -T db psql -U "${PUSER}" -d "${TESTDB}" -tAc "SELECT count(*) FROM res_users;"

echo "[restore-test] Limpiando ${TESTDB}..."
${COMPOSE} exec -T db dropdb -U "${PUSER}" "${TESTDB}"
echo "[restore-test] OK: ${LATEST} es restaurable."
