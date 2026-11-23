# Imagen propia de Odoo 19 CE para MPRepuestos.
# Base oficial (Ubuntu noble) → ya trae wkhtmltopdf parcheado.
FROM odoo:19

USER root

# Dependencias de SISTEMA antes del pip:
#  - swig/libssl-dev/python3-dev/build-essential/pkg-config: M2Crypto compila contra OpenSSL.
#  - git: instalar pyafipws desde su repositorio (fork filoquin@py3k).
#  - postgresql-client: chequeo idempotente de existencia de la base en el bootstrap.
#  - gettext-base: provee `envsubst` para inyectar secretos en odoo.conf en runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        swig \
        libssl-dev \
        python3-dev \
        build-essential \
        pkg-config \
        git \
        postgresql-client \
        gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python. --break-system-packages: la base noble es PEP 668 (entorno gestionado).
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# El bootstrap genera /etc/odoo/odoo.conf desde el template en runtime → dir escribible por odoo.
RUN mkdir -p /etc/odoo && chown odoo /etc/odoo

USER odoo

# Seguridad (23/11/2026), CVE-2026-130029: XSS en el sanitizador de HTML de Odoo.
# 1) Arreglo de Odoo del 16/11/2026 en odoo/tools/mail.py (commit 8196ff1a73f9 de la rama 19.0).
# 2) lxml 5.2.1 de pip, que trae libxml2 2.12 (la del sistema es 2.9.14): es la mitigacion que da el
#    aviso (libxml2 >= 2.10). Queda en /usr/local, que tiene prioridad sobre el lxml de apt.
# Si algo no queda aplicado, el build falla. Sobra cuando la base oficial traiga el arreglo.
USER root
COPY cve/ /tmp/cve/
RUN patch -p1 --forward --no-backup-if-mismatch -d /usr/lib/python3/dist-packages < /tmp/cve/odoo19-mail-20261116.patch \
 && grep -qF 'serialized = serialized.replace' /usr/lib/python3/dist-packages/odoo/tools/mail.py \
 && pip3 install --no-cache-dir --break-system-packages --ignore-installed --no-deps lxml==5.2.1 \
 && python3 -c "import sys, lxml.etree as e; v = e.LIBXML_VERSION; print('libxml2', v); sys.exit(0 if v >= (2, 10, 0) else 'libxml2 < 2.10')" \
 && rm -rf /tmp/cve
USER odoo
