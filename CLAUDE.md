# CLAUDE.md — Instrucciones para Claude Code

> Este archivo lo carga Claude Code automáticamente al abrir el repo.
> El detalle largo está en [`docs/CONTEXTO.md`](docs/CONTEXTO.md) y [`docs/ARCA-FACTURA-ELECTRONICA.md`](docs/ARCA-FACTURA-ELECTRONICA.md).
> **Leé los dos antes de tocar nada de facturación electrónica.**

---

## Qué es este proyecto

Migración de **MPRepuestos** desde **Odoo Online 19 Enterprise (SaaS)** hacia un **VPS propio con Odoo 19 Community en Docker**.

**Objetivo central del proyecto:** emitir **factura electrónica ARCA (ex-AFIP) desde el Punto de Venta**. Todo lo demás es soporte para eso.

El módulo oficial de FE (`l10n_ar_edi`) es **Enterprise** y no existe en Community. La solución elegida es un **forward-port propio** de los módulos AGPL de ADHOC (18 → 19), vendoreados en `addons/custom/`.

---

## 🗣️ Idioma

**Siempre responder en español rioplatense**, con ortografía completa (tildes, ñ, ¿?, ¡!).
Los términos técnicos e identificadores de código quedan en su forma original (`account.move`, `l10n_ar_afip_pos_number`, etc.).

---

## ⚠️ Reglas de trabajo (NO negociables)

### 1. La configuración por UI la hace Renzo, no vos

Renzo **quiere aprender Odoo**, no solo que funcione.

- ✅ **Vos hacés:** instalar módulos, resolver dependencias, editar código, tocar `addons_path`, levantar/reiniciar contenedores, diagnosticar por logs y `psql`.
- ❌ **Vos NO hacés:** configurar por SQL/shell nada que tenga pantalla en la UI — compañía, plan de cuentas, diarios, impuestos, datos fiscales, usuarios, puntos de venta, PoS.
- 🎯 **En su lugar:** guiá paso a paso. Decí el menú exacto (`Contabilidad → Configuración → Diarios`), qué significa cada campo, qué elegir y **por qué**. Después esperá que él confirme.

Renzo va a **mandar capturas de pantalla** cuando se pierda. Leelas y ubicalo en el paso que corresponde.

Leer por SQL para diagnosticar está perfecto. **Escribir** por SQL lo que se configura por UI, no.

### 2. Prohibido usar código de Odoo Enterprise como fuente

La **OEEL** (licencia de Enterprise) es propietaria: prohíbe copiar, redistribuir o derivar sin suscripción activa. Un sistema que emite comprobantes fiscales ante ARCA **no puede tener esa exposición legal**.

Fuentes válidas, y son suficientes:

| Fuente | Licencia |
|---|---|
| ADHOC `odoo-argentina*` (nuestra base vendoreada) | AGPL-3 |
| OCA `l10n_ar_arca_edi` (reimplementación ARCA-nativa, gran referencia) | AGPL-3 |
| `point_of_sale` de Community | LGPL |
| Documentación pública de Odoo | Pública |

Estudiar documentación pública y código open source = legal. Copiar fuente propietaria de Enterprise = no. **La distinción es de licencia, no técnica.**

### 3. Verificá antes de "arreglar"

Buena parte de lo que un análisis estático marca como "roto en v19" son **falsos positivos**. Antes de tocar código del forward-port, comprobá contra el core real dentro del contenedor. Ver la tabla de falsos positivos ya confirmados en [`docs/CONTEXTO.md`](docs/CONTEXTO.md).

---

## 🖥️ Infraestructura

| Ítem | Valor |
|---|---|
| VPS | Hostinger — `72.60.156.201` (IPv6 `2a02:4780:66:db86::1`) |
| URL productiva | **https://mp.dakodev.com** (SSL Let's Encrypt vía NPM, Force SSL) |
| Proyecto compose | `mprepuestos` |
| Contenedores | `mprepuestos_odoo`, `mprepuestos_db` |
| Base de datos | `mprepuestos` (usuario `odoo`) |
| Login app | `admin` / `admin` — ⚠️ **pendiente de cambiar** |
| Master DB password | en `docker/.env` (gitignored) |
| Reverse proxy | NGINX Proxy Manager preexistente: contenedor `nginx-app-1`, red `nginx_default` |
| Repo de referencia | `/root/projects/renzo_odoo` — otro Odoo de Renzo, de donde salieron los módulos UX |

> ⚠️ Los puertos 8069/8072 **no están publicados al host**. El acceso es solo vía NPM. Si hace falta reabrirlos temporalmente, volver a agregar el bloque `ports:` en `docker/docker-compose.yml` con `HTTP_PORT`/`GEVENT_PORT` del `.env`.
>
> ⚠️ `nginx-app-1` es **infra compartida** (sirve otros sitios). Un `nginx -s reload` ahí impacta a terceros: pedí autorización antes.

---

## 💻 Modo remoto — Claude Code desde la notebook

Si estás corriendo **en la notebook de Renzo** (no dentro del VPS), Odoo **no está en tu máquina**. El acceso es por SSH con el alias `mp`:

```bash
ssh mp "docker ps"
```

> Si `ssh mp` te pide contraseña, **no está configurada la clave** y no vas a poder automatizar nada — avisale a Renzo antes de seguir. Ver `docs/CONTEXTO.md` §10.

### El loop de trabajo

El código vive en **dos lugares** y se sincroniza por GitHub:

```
  NOTEBOOK                    GITHUB                      VPS
  ────────                    ──────                      ───
  editás el código
  git commit + push  ────────────►  master  ──────────►  ssh mp "git pull"
                                                          + restart odoo
                                                                 │
  ssh mp "logs / psql / odoo shell"  ◄──────────────────────────┘
```

- **Editar código** → en la notebook.
- **Probar** → en el VPS por SSH (ahí corre Odoo con las dependencias de ARCA).
- **Nunca** hagas commits desde el VPS. El VPS solo hace `git pull`.

Para correr cualquiera de los comandos de abajo en remoto, prefijalos con `ssh mp "cd /root/projects/mp_repuestos_odoo && ..."`.

---

## 🔧 Comandos operativos

> Estos son **tal como se corren dentro del VPS**. Desde la notebook, envolvelos en `ssh mp "..."`.

```bash
cd /root/projects/mp_repuestos_odoo

# Instalar / actualizar módulos (NO reinicia el registry por sí solo)
docker compose -p mprepuestos exec -T odoo \
  odoo -c /etc/odoo/odoo.conf -d mprepuestos -i <modulos> --no-http --stop-after-init

# Actualizar
docker compose -p mprepuestos exec -T odoo \
  odoo -c /etc/odoo/odoo.conf -d mprepuestos -u <modulos> --no-http --stop-after-init

# ⚠️ SIEMPRE después de instalar/actualizar: recarga el registry en memoria
docker compose -p mprepuestos restart odoo

# Logs
docker compose -p mprepuestos logs -f --tail=100 odoo

# Consultas a la base
docker exec mprepuestos_db psql -U odoo -d mprepuestos -c "SELECT ..."

# Odoo shell (el server en vivo ocupa el puerto → hay que usar --no-http)
docker compose -p mprepuestos exec -T odoo \
  odoo shell -c /etc/odoo/odoo.conf -d mprepuestos --no-http < script.py
```

`docker/entrypoint-bootstrap.sh` **regenera `/etc/odoo/odoo.conf` desde el template en cada arranque** (vía `envsubst`). Por eso alcanza con `restart` para tomar cambios de `docker/odoo.conf` — no hace falta rebuild.

---

## 🪤 Gotchas que ya nos costaron tiempo

1. **Registry stale.** Instalar módulos con `docker exec` corre en **otro proceso**; el servidor en vivo se queda con el registry viejo y la UI tira `KeyError: '<campo nuevo>'` o `OwlError: field is undefined`. → **Siempre `restart` después de instalar/actualizar**, y decile a Renzo que haga `Ctrl+Shift+R`.

2. **`odoo shell` en vivo falla** con *"Address already in use"* (intenta bindear 8069). → usar `--no-http` y pasar el script por stdin.

3. **`res_users` no tiene columna `lang` en v19** (es related a `partner_id.lang`). Para cambiar idioma por SQL hay que tocar `res_partner.lang` del partner del usuario. El default de nuevos partners está en `ir_default`.

4. **WebSocket / marco amarillo.** El checkbox *"Websockets Support"* del NPM **solo agrega headers** al `location /` (que va a :8069); **no rutea `/websocket` al puerto gevent**. Sin eso Odoo tira `RuntimeError: Couldn't bind the websocket... evented port (8072)` y pinta el borde amarillo de "conexión perdida".
   **Fix aplicado:** bloque `location /websocket { proxy_pass http://mprepuestos_odoo:8072; ... }` en `/data/nginx/proxy_host/22.conf` dentro de `nginx-app-1` (backup en `22.conf.bak`).
   ⚠️ **El NPM regenera ese archivo si se edita el Proxy Host desde su UI.** Para que persista hay que pegar el bloque en la pestaña **Advanced → Custom Nginx Configuration**. **Esto todavía está pendiente** — si vuelve el marco amarillo, es esto.

5. **`--update-list` no existe** como opción del CLI de Odoo.

6. **`size=` en `fields.Char` sigue siendo válido en v19.** El core lo usa (`res_country.py`, `res_currency.py`). No lo "arregles".

---

## 📁 Estructura del repo

```
addons/
  custom/          ← módulos propios y vendoreados (EDITABLES)
    l10n_ar_afipws         ← base WSAA/certificados ARCA   (forward-port 18→19) ✅
    l10n_ar_afipws_fe      ← FE sobre account.move          (forward-port 18→19) ✅
    l10n_ar_pos_afipws_fe  ← FE desde PoS                   (SIN portar todavía) ⬜
    web_responsive         ← OCA, look tipo Enterprise
    dako_password          ← gestor de contraseñas
  external/        ← submódulos git PINEADOS (read-only, no parchear acá)
docker/            ← Dockerfile, compose, odoo.conf (template), requirements, bootstrap
scripts/           ← backup.sh, restore-test.sh
docs/              ← CONTEXTO.md + ARCA-FACTURA-ELECTRONICA.md
```

**Nunca parchees `addons/external/`**: son submódulos; los cambios se pierden en el próximo `git pull`. Si hay que tocar un módulo de terceros, **vendorizalo a `addons/custom/`** y quitá el repo original del `addons_path` para evitar colisión de nombres en el registry.

---

## 🔐 Seguridad

- `docker/.env` está gitignored (`POSTGRES_PASSWORD`, `ODOO_MASTER_PASSWD`). Plantilla en `docker/.env.example`.
- `.gitignore` excluye `*.crt`, `*.key`, `*.pem`: **las claves privadas y certificados de ARCA nunca se commitean.**
- ⚠️ **Este repo es público** y la instancia está expuesta en HTTPS con `admin`/`admin`. **Cambiar esa contraseña es la tarea de seguridad más urgente del proyecto.**

---

## 🎯 Dónde estamos

Ver el estado completo en [`docs/CONTEXTO.md`](docs/CONTEXTO.md).

**Resumen:** Fases 0, 1 y 2 completas. El backend de FE ARCA ya está portado e instalado. Estamos en el **trámite de certificado + alta de punto de venta en ARCA** (Renzo, por portal). Después: probar CAE en homologación, y recién ahí encarar el PoS.

**El próximo paso concreto está al final de [`docs/ARCA-FACTURA-ELECTRONICA.md`](docs/ARCA-FACTURA-ELECTRONICA.md).**
