#!/usr/bin/env bash
# Bootstrap idempotente del contenedor Odoo de MPRepuestos:
#  1) Genera /etc/odoo/odoo.conf desde el template inyectando secretos.
#  2) En el PRIMER arranque (base inexistente): inicializa la base sin demo
#     y fija el usuario admin con login/password deterministas.
#  3) Cede a Odoo como server long-running.
set -euo pipefail

CONF=/etc/odoo/odoo.conf
TEMPLATE=/etc/odoo/odoo.conf.template

echo "[bootstrap] Generando ${CONF} desde template..."
# Solo se sustituyen estas variables (protege el ancla regex final de dbfilter).
envsubst '$ODOO_MASTER_PASSWD $POSTGRES_USER $POSTGRES_PASSWORD $DB_NAME' \
    < "${TEMPLATE}" > "${CONF}"

echo "[bootstrap] Verificando si la base '${DB_NAME}' existe..."
DB_EXISTS=$(PGPASSWORD="${PASSWORD}" psql -h "${HOST}" -U "${USER}" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" 2>/dev/null || true)

if [ "${DB_EXISTS}" != "1" ]; then
    echo "[bootstrap] Base '${DB_NAME}' no existe → inicializando (sin datos demo)..."
    odoo -c "${CONF}" -d "${DB_NAME}" -i base --without-demo=True --stop-after-init

    echo "[bootstrap] Fijando usuario admin (login=${ADMIN_LOGIN})..."
    odoo shell -c "${CONF}" -d "${DB_NAME}" <<PYEOF
admin = env.ref('base.user_admin')
admin.login = "${ADMIN_LOGIN}"
admin.password = "${ADMIN_PASSWORD}"
env.cr.commit()
print("[bootstrap] admin OK: login=%s" % admin.login)
PYEOF
else
    echo "[bootstrap] Base '${DB_NAME}' ya existe → omito init (idempotente)."
fi

echo "[bootstrap] Iniciando Odoo..."
exec odoo -c "${CONF}"
