# Contexto del proyecto MPRepuestos — estado completo

> Documento de traspaso. Contiene todo lo que se decidió, se investigó y se rompió/arregló hasta hoy.
> Complemento operativo: [`ARCA-FACTURA-ELECTRONICA.md`](ARCA-FACTURA-ELECTRONICA.md).
> Reglas de trabajo: [`../CLAUDE.md`](../CLAUDE.md).

**Última actualización:** 22 de julio de 2026

---

## 1. El proyecto en una frase

Sacar a MPRepuestos de **Odoo Online 19 Enterprise (SaaS)** y ponerlo en un **VPS propio con Odoo 19 Community en Docker**, con el objetivo central de **facturar electrónicamente ante ARCA desde el Punto de Venta**.

### Por qué esto no es trivial

La facturación electrónica argentina oficial de Odoo (`l10n_ar_edi`) es **exclusiva de Enterprise**. En Community **no existe**. Las opciones eran:

| Opción | Veredicto |
|---|---|
| Pagar Enterprise | Descartada (es justamente lo que se está dejando) |
| Bajar a Odoo 18 (donde ADHOC sí tiene FE) | Descartada (arrancar migrando hacia atrás) |
| Copiar el código de Enterprise | **Ilegal** — ver §2 |
| **Forward-port propio de los módulos AGPL de ADHOC (18 → 19)** | ✅ **Elegida** |

Otras empresas ya operan FE argentina en Odoo 19 Community, así que el camino está probado. ADHOC dejó el port **iniciado pero sin liberar**.

---

## 2. Restricción legal (no negociable)

**No se usa código de Odoo Enterprise como fuente.** La **OEEL** (Odoo Enterprise Edition License) es propietaria y prohíbe copiar, redistribuir o derivar sin suscripción activa. Un sistema que emite comprobantes fiscales oficiales ante ARCA no puede cargar esa exposición legal.

Fuentes válidas — y alcanzan para el 100% de lo necesario, **incluido el PoS**:

- ADHOC `odoo-argentina` / `odoo-argentina-ce` — **AGPL-3** (nuestra base vendoreada)
- OCA `l10n_ar_arca_edi` — **AGPL-3** (reimplementación ARCA-nativa moderna; excelente referencia de patrones y tests)
- `point_of_sale` de Odoo Community — **LGPL** (legible y extensible)
- Documentación pública de Odoo y de ARCA

> Estudiar documentación pública y código open source = legal.
> Copiar fuente propietaria de Enterprise = no.
> **La distinción es de licencia, no técnica.**

---

## 3. Estado por fase

| Fase | Descripción | Estado |
|---|---|---|
| 0 | Resguardo del origen (export SaaS) | ✅ |
| 1 | VPS + infraestructura Docker | ✅ |
| 2 | Localización AR + módulos base | ✅ |
| 3 | Migración de datos maestros | ⬜ (despriorizada a propósito) |
| 4 | **Facturación electrónica ARCA** | 🔄 **en curso** |
| 5 | Operación asistida / paralelo | ⬜ |
| 6 | Go-live + corte | ⬜ |
| — | Hardening / backups / DNS-SSL | 🟨 parcial |

**Decisión explícita:** la Fase 4 (FE) se puso **antes** que la Fase 3 (datos maestros), porque la FE es el objetivo del proyecto y el riesgo técnico real. Los datos maestros son trabajo mecánico y predecible.

---

## 4. Infraestructura

| Ítem | Valor |
|---|---|
| VPS | Hostinger — `72.60.156.201` (IPv6 `2a02:4780:66:db86::1`) |
| URL productiva | https://mp.dakodev.com |
| SSL | Let's Encrypt vía NGINX Proxy Manager, Force SSL |
| Reverse proxy | NPM preexistente: contenedor `nginx-app-1`, red `nginx_default` |
| Proyecto compose | `mprepuestos` |
| Contenedores | `mprepuestos_odoo`, `mprepuestos_db` |
| Base | `mprepuestos`, usuario `odoo` |
| Login app | `admin` / `admin` ⚠️ pendiente de cambiar |
| Imagen | oficial `odoo:19` personalizada (`docker/Dockerfile`) — Ubuntu noble, Python 3.12 |
| PostgreSQL | 16, volumen persistente |

> `curl ifconfig.me` devuelve la **IPv6**. Para la IPv4 usar `ipinfo.io/ip`.

Los puertos 8069/8072 **no están publicados al host** — se quitó el bloque `ports:` del compose después de validar HTTPS. El acceso es solo por el NPM.

### Bootstrap

`docker/entrypoint-bootstrap.sh` es idempotente: inicializa la DB si no existe y **regenera `/etc/odoo/odoo.conf` desde el template en cada arranque** (`envsubst`). Por eso un cambio en `docker/odoo.conf` se toma con un simple `restart`, sin rebuild.

### El fix del WebSocket (marco amarillo)

**Síntoma:** borde amarillo en toda la ventana de Odoo + cartel de "conexión en tiempo real perdida".

**Causa raíz:** el checkbox *"Websockets Support"* del NPM **solo agrega los headers `Upgrade`/`Connection` al `location /`** (que apunta a `:8069`). **No crea el ruteo de `/websocket` al puerto gevent `:8072`.** Odoo 19 tira:

```
RuntimeError: Couldn't bind the websocket. Is the connection opened on the evented port (8072)?
werkzeug ... "GET /websocket" 500
```

**Fix aplicado:** bloque dedicado insertado en `/data/nginx/proxy_host/22.conf` dentro de `nginx-app-1` (backup en `22.conf.bak`), antes de `location / {`:

```nginx
location /websocket {
  proxy_pass http://mprepuestos_odoo:8072;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_http_version 1.1;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-Host $host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_read_timeout 720s;
  proxy_send_timeout 720s;
}
```

**Verificado:** el log pasó de `werkzeug ... 500` a `longpolling ... 8072`, y el handshake devuelve `HTTP 101 Switching Protocols`.

> ⚠️ **PENDIENTE:** el NPM **regenera ese archivo** si se edita el Proxy Host desde su interfaz web. Para que persista hay que pegar el bloque en la pestaña **Advanced → Custom Nginx Configuration** del Proxy Host. **Todavía no se hizo.** Si vuelve el marco amarillo, es esto.
>
> ⚠️ `nginx-app-1` sirve **otros sitios**. Un `nginx -s reload` impacta a terceros: pedir autorización antes.

---

## 5. Localización argentina

Hay **dos ecosistemas conviviendo**, y es importante no confundirlos:

### 5.1 `l10n_ar` oficial de Odoo Community

Viene en la imagen (`/usr/lib/python3/dist-packages/odoo/addons/l10n_ar`, versión 3.7). **Instalable y funcionando.** Aporta:

- Planes de cuenta: `ar_base` (Monotributo, 227 cuentas), `ar_ex` (Exento, 290), **`ar_ri` (Responsable Inscripto, 298→313)**
- Tipos de comprobante AFIP con letras (A/B/C/E/M)
- Impuestos IVA, responsabilidades AFIP, `_l10n_ar_get_amounts`, `ensure_vat`

### 5.2 Ecosistema ADHOC (submódulos git)

ADHOC tiene **dos repos** con roles distintos:

| Repo | Qué es | Estado en 19.0 |
|---|---|---|
| `ingadhoc/odoo-argentina` | Funcionalidad base que no está ni en CE ni en EE | ✅ **Todo portado, `installable=True`** |
| `ingadhoc/odoo-argentina-ce` | Lo que en Odoo está en Enterprise — **acá vive la FE** | ❌ Port iniciado, **no liberado** |

En `odoo-argentina-ce`, el commit `a81ddf8 "[UPD] Initialize version 19.0"` (25-sep-2025) creó la rama, pero los módulos FE siguen con `version 18.0.x` + `installable=False`, **idéntico en `19.0` y `staging.19.0`**. Nuestro submódulo está pineado a `f9b14ad` = HEAD real de la rama 19.0 — **no estamos desactualizados, ADHOC simplemente no lo liberó**.

### 5.3 Configuración fiscal aplicada

- Condición: **IVA Responsable Inscripto**
- Plan de cuentas **`ar_ri`** cargado — 313 cuentas, 155 impuestos, 9 diarios, 4 posiciones fiscales
- País fiscal = AR · IVA por defecto Ventas/Compras = 21%
- Idioma `es_AR` activo por defecto

> **🪤 Gotcha importante y contraintuitivo:** el tipo de identificación **CUIT no se puede seleccionar hasta que el plan de cuentas argentino esté cargado.**
> La vista `l10n_latam_base/views/res_partner_view.xml:18` tiene:
> ```xml
> invisible="is_vat and 'LATAMID' not in fiscal_country_group_codes"
> ```
> Es decir: el campo está **oculto** mientras el país fiscal siga siendo el default (US). No es un bug ni un permiso — es orden de operaciones.
> **Orden correcto: 1) cargar plan de cuentas `ar_ri` → 2) el país fiscal pasa a AR → 3) recién ahí aparece CUIT (y se autocompleta).**

---

## 6. Contabilidad en Community: el stack OCA

**Odoo 19 Community NO tiene la app "Contabilidad"** (`account_accountant`, Enterprise). Solo trae **"Facturación"** (`account`).

Lo importante: **el motor contable es el mismo**. Lo que falta en CE es la capa de *reportes* y *conciliación*. Eso lo repone OCA, gratis:

| Módulo OCA | Qué repone |
|---|---|
| `account_financial_report` | **Libro Mayor, Balance de Sumas y Saldos, Aged Partner Balance, Open Items, Journal Ledger, VAT Report** — el más importante |
| `account_tax_balance` + `partner_statement` | Balance de impuestos (IVA) + extractos de cuenta |
| `account_reconcile_oca` + `account_statement_base` | **Widget de conciliación bancaria estilo Enterprise** — lo que más se extraña al pasar de EE a CE |
| `mis_builder` (+ `date_range`) | Balance General / Estado de Resultados configurables, KPIs |

Todos instalados y funcionando. **No es una app única "Contabilidad": es `account` + estos addons.**

### Submódulos en `addons/external/` (todos pineados)

| Repo | SHA | Para qué |
|---|---|---|
| `odoo-argentina` | — | Base AR de ADHOC |
| `odoo-argentina-ce` | `f9b14ad` | ⚠️ **fuera del `addons_path`** (ver §7.1) |
| `account-invoicing` | `db80423` | `account_background_post` (dep de `account_ux`) |
| `account-financial-reporting` | `161c9fa` | Reportes contables |
| `account-reconcile` | `045dca4` | Conciliación bancaria |
| `mis-builder` | `5e2e00f` | Estados contables |
| `server-ux` | `769be94` | `date_range` |
| `account-payment`, `account-financial-tools`, `reporting-engine` | — | Fase 1/2 |

---

## 7. El forward-port de la FE (Fase 4)

### 7.1 Estrategia de packaging

Los 3 módulos FE **se vendorizaron** de `addons/external/odoo-argentina-ce/` a **`addons/custom/`**, porque un submódulo git es read-only: parchearlo ahí genera conflictos en cada `git pull`.

Y **`external/odoo-argentina-ce` se quitó del `addons_path`** para evitar colisión de nombres en el registry (los mismos módulos existirían dos veces). No se pierde nada: su único otro módulo, `l10n_ar_reports`, sigue en 16.0/uninstallable.

Esto está documentado dentro del propio `docker/odoo.conf`.

`pyafipws` se **pineó a un commit fijo** (`0bb5988b31f066ca1906156183a3a0888643c314` del fork `filoquin@py3k`, compatible con Python 3.12) en `docker/requirements.txt`, para que un rebuild no traiga cambios silenciosos del WSDL/API de ARCA.

> ⚠️ El pin **todavía no se aplicó a la imagen corriendo** (requiere rebuild). La imagen actual ya tiene un pyafipws funcionando.

### 7.2 Estado por etapa

| Etapa | Qué es | Estado |
|---|---|---|
| 0 | Vendorizar + sanity del registry | ✅ |
| A | `l10n_ar_afipws` instalable (base WSAA/certificados) | ✅ `19.0.1.0.0` instalado |
| B | `l10n_ar_afipws_fe` + FE desde `account.move` | ✅ `19.0.2.0.0` instalado — **falta validar con CAE real** |
| C | `l10n_ar_pos_afipws_fe` + FE desde PoS | ⏸️ **pausada** — el difícil |
| D | Tests + hardening | ⬜ |

**Validación de runtime hecha** (vía `odoo shell`): 11 campos AFIP en `account.move`, `_compute_qr_code`, `do_pyafipws_request_cae`, `get_related_invoices_data`, `_l10n_ar_get_amounts`, `res.company.get_connection` / `get_key_and_certificate` / `_get_environment_type`, `account.journal.afip_ws` / `l10n_ar_afip_pos_number`.

**Pre-test de generación de CSR** hecho con `env.cr.rollback()` (nada persistió): clave privada 1704 bytes, CSR con cabecera `-----BEGIN CERTIFICATE REQUEST-----`. **El port funciona** antes de pedirle a nadie que apriete botones.

### 7.3 Fixes reales aplicados

| Archivo | Fix | Por qué |
|---|---|---|
| `l10n_ar_afipws/models/res_company.py:~247` | `sys.exc_type`/`sys.exc_value` → `traceback.format_exception_only(type(e), e)[0]` | Esos atributos **no existen en Python 3** |
| `l10n_ar_afipws/views/res_partner.xml` | Ancla de vista `accounting_entries` → `fiscal_information` | El grupo `accounting_entries` **fue removido en v19** |
| 6 campos en `afipws_certificate*.py`, `afipws_connection.py`, `res_company.py` | Quitado `auto_join=True` | **Removido en v19** |
| `l10n_ar_afipws_fe/models/account_move.py:18` | Quitado el monkeypatch `base64.encodestring = base64.encodebytes` → uso directo de `encodebytes` | `encodestring` **fue removido en Python 3.9** |
| `l10n_ar_afipws_fe/models/res_config_settings.py` | Quitado `selection=` de un campo `related` | En v19 se ignora y emite warning |
| ambos `__manifest__.py` | `version` 18.0.x → 19.0.x, `installable: False` → `True` | — |
| `l10n_ar_afipws/views/res_config_settings.xml` | Reescrito con el patrón nativo de ajustes de Odoo | Se veía apretado, en dos renglones |

### 7.4 ⚠️ Falsos positivos — NO los "arregles"

Un análisis estático marcó estos como críticos. **Se verificaron uno por uno contra el core real del contenedor y son correctos como están:**

| "Problema" | Realidad |
|---|---|
| `size=` en `fields.Char` "removido en v19" | ❌ **Sigue válido.** El core lo usa: `res_country.py:41 size=2`, `res_currency.py:27 size=3` |
| Doble `@api.onchange("company_id")` | ❌ Los dos se ejecutan bien en Odoo. No es un bug |
| `pos.order.refunded_order_id` "debería ser plural" | ❌ El singular es **correcto** en el core de v19 |
| `external_dependencies: "OpenSSL"` "debería ser pyOpenSSL" | ❌ `OpenSSL` es el **nombre importable**; cambiarlo **rompería** la verificación de dependencias de Odoo |

> **Lección:** verificar contra el core dentro del contenedor antes de tocar. Varios "riesgos críticos" del recon inicial redujeron el estimado del port de forma material.

### 7.5 Etapa C (PoS) — lo que viene y por qué es el difícil

`l10n_ar_pos_afipws_fe` tiene **53 líneas de Python y CERO frontend** (`static/` vacío). El ticket con CAE, vencimiento y QR **hay que construirlo desde cero** en OWL contra la arquitectura del PoS de v19 (store reactivo, hooks, template como propiedad `static`, sin JS inline por CSP).

**Decisiones ya tomadas por Renzo:**

1. **Facturar solo cuando el cliente lo pide** — no toda venta. El flujo síncrono bloqueante contra ARCA aplica únicamente al path "facturar", no a cada cobro. (Importante para la performance de la caja.)
2. **Soportar Factura B/C (consumidor final) Y Factura A (RI)** → hay que agregar selección de cliente con datos fiscales en la pantalla del PoS.

Riesgos principales: el frontend OWL es **desarrollo nuevo, no port**; y el momento de lectura del CAE dentro del flujo de facturación asíncrona del PoS.

---

## 8. Cambios en Odoo 19 que importan para este port

| Cambio | Detalle |
|---|---|
| `auto_join` | **Removido** de campos relacionales |
| `groups_id` → `group_ids` | Renombrado |
| `<tree>` → `<list>` | Vistas de lista |
| `attrs=` | **Removido** — se usan atributos directos (`invisible="..."`, `readonly="..."`) |
| `name_get` → `_compute_display_name` | — |
| `size=` en `fields.Char` | ✅ **Sigue válido** |
| PoS | Refactor OWL: hooks, template `static`, store reactivo |
| `res_users.lang` | Ya no es columna: es related a `partner_id.lang` |

---

## 9. Errores que ya nos pasaron (y cómo se resolvieron)

| Error | Causa | Fix |
|---|---|---|
| `KeyError: 'l10n_ar_afip_fce_transmission'` al entrar a Ajustes / `OwlError: field is undefined` | **Registry stale**: se instaló por `docker exec` (otro proceso) y el server en vivo quedó con el registry viejo | `docker compose -p mprepuestos restart odoo` + `Ctrl+Shift+R` en el navegador |
| `UserError: el módulo "account_ux" depende de "account_background_post"` | Ese módulo vive en `ingadhoc/account-invoicing`, que no estaba como submódulo | Agregado y pineado a `db80423`, sumado al `addons_path` |
| Compañía con plan de cuentas `generic_coa` y país US | Se autocargó al instalar `account` | Cargar `ar_ri` desde la UI |
| "No me deja elegir CUIT" | El campo está oculto mientras el país fiscal sea US | Ver el gotcha de §5.3 — es orden de operaciones |
| `odoo shell` → "Address already in use" | Intenta bindear el 8069, ocupado por el server en vivo | Usar `--no-http` y pasar el script por stdin |
| `--update-list` no reconocido | **No es una opción válida** del CLI de Odoo | Los módulos aparecen igual tras el restart |
| `git push` → "Password authentication is not supported" | GitHub ya no acepta contraseña | Usar Personal Access Token o `gh auth login` |

---

## 10. Deuda pendiente

### Seguridad (urgente)
- [ ] **Cambiar la contraseña de `admin`** (hoy `admin`/`admin`, sobre HTTPS público)
- [ ] **SSH:** hoy `PermitRootLogin yes` + `PasswordAuthentication yes`, **sin firewall** y sin fail2ban, con IP pública fija
- [ ] Rotar la contraseña de root del VPS
- [ ] Activar `ufw` (22/80/443) e instalar `fail2ban`

### Infraestructura
- [ ] **Persistir el bloque `/websocket`** en la pestaña *Advanced* del Proxy Host del NPM (hoy solo está en el archivo generado, que el NPM puede pisar)
- [ ] Cron de backups (`scripts/backup.sh` diario + `restore-test.sh` semanal)
- [ ] Backup off-site (rclone)
- [ ] Rebuild de la imagen para aplicar el pin de `pyafipws`

### Producto
- [ ] Terminar Fase 4 (ver [`ARCA-FACTURA-ELECTRONICA.md`](ARCA-FACTURA-ELECTRONICA.md))
- [ ] Etapa C: PoS con FE
- [ ] Etapa D: tests (mock de pyafipws; refund de PoS con `reversed_entry_id`), usando los 44 tests de OCA `arca_edi` como especificación
- [ ] Fase 3: migración de datos maestros
- [ ] Evaluar contribuir los fixes upstream a ADHOC (reduce mantenimiento futuro)
