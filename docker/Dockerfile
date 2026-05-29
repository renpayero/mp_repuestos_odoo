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
