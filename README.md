# MPRepuestos — Migración Odoo 19 (Online Enterprise → VPS Community)

> **Hoja de ruta de ejecución con checklist.** Cuando todas las casillas de este documento estén marcadas, el [plan de migración](./plan-migracion-mprepuestos-odoo19.md) está cumplido.
>
> Este README es el **mapa de trabajo del repositorio**. El plan describe el *qué* y el *por qué*; este README describe el *cómo* y el *estado*. Cada bloque referencia la sección del plan que lo respalda (`→ Plan §N`).

**Origen:** Odoo 19.0.1.3 Online/SaaS (Enterprise) · **Destino:** Odoo 19.0 Community en VPS Hostinger, todo en Docker
**Objetivo central:** facturación electrónica ARCA (WSFEv1) desde el Punto de Venta · **Contabilidad:** limpia desde cero (RI) · **Sin historial transaccional**

---

## 0. Cómo usar este checklist

- `[ ]` pendiente · `[x]` hecho y verificado · `[~]` en progreso (editar a mano si hace falta)
- **No marcar "hecho" sin verificar.** Cada fase tiene su criterio de aceptación ("✅ DoD" = *Definition of Done*).
- Las tareas que **dependen de terceros** (contador / Clave Fiscal) están marcadas con 🔗**(externo)**.
- Las tareas de **código propio** (migración de módulos OCA, módulo custom) están marcadas con 🛠️**(dev)**.
- El orden de las fases es secuencial salvo donde se indique que pueden solaparse.

### Estado global

| Fase | Descripción | Estado |
|---|---|---|
| 0 | Resguardo del origen | ⬜ Pendiente |
| 1 | VPS + Infraestructura Docker | ⬜ Pendiente |
| 2 | Baseline Community (módulos + config RI) | ⬜ Pendiente |
| 3 | Datos maestros (productos + contactos) | ⬜ Pendiente |
| 4 | FE + PoS en homologación | ⬜ Pendiente |
| 5 | Pase a producción | ⬜ Pendiente |
| 6 | Post go-live (aprendizaje + hardening) | ⬜ Pendiente |

> Actualizar el emoji de estado (⬜ Pendiente / 🟨 En progreso / ✅ Completo) a medida que se cierra cada fase.

---

## Estructura propuesta del repositorio

```
mp_repuestos_odoo/
├── README.md                         # este archivo (hoja de ruta)
├── plan-migracion-mprepuestos-odoo19.md
├── docker/
│   ├── Dockerfile                    # imagen propia sobre odoo:19 (deps Python+sistema, addons)
│   ├── docker-compose.yml            # db (pg16) + odoo — SIN proxy propio (usa el NPM existente del server)
│   ├── .env.example                  # variables (passwords, puertos) — el real NO se commitea
│   ├── odoo.conf                     # config Odoo (montado en el contenedor)
│   └── requirements.txt              # pyafipws(filoquin), M2Crypto, pysimplesoap, xlrd, ...
├── addons/                           # repos de terceros + módulos propios
│   ├── odoo-argentina-ce/            # submódulo o copia (rama 19.0)
│   ├── odoo-argentina/               # submódulo o copia (rama 19.0)
│   ├── account-payment/              # submódulo o copia (rama 19.0)
│   ├── account-financial-tools/      # submódulo o copia (rama 19.0)
│   ├── reporting-engine/             # submódulo o copia (rama 19.0)  → report_xlsx
│   ├── pos_session_pay_invoice/      # 🛠️ migrado OCA 18→19 (cobro cc en PoS)
│   ├── account_cash_invoice/         # 🛠️ migrado OCA 18→19 (dependencia)
│   └── mp_pos_settle_due/            # 🛠️ módulo propio (Plan B, si hace falta)
├── data/                             # migración de datos maestros
│   ├── export/                       # CSV/XML exportados del Online (read-only)
│   ├── import/                       # CSV preparados para cargar en Community
│   └── scripts/                      # XML-RPC / transformación de datos
├── scripts/
│   ├── backup.sh                     # pg_dump + filestore → almacenamiento externo
│   └── restore-test.sh               # prueba periódica de restore
└── docs/
    ├── checklist-contador.md         # extracto §6.1 para entregar al contador
    ├── runbook-produccion.md         # corte, rollback, troubleshooting
    └── manual-cajero.md              # uso diario del PoS (facturar/no facturar, cobrar cc)
```

> **Decisión a tomar al iniciar Fase 1:** ¿submódulos git (`git submodule`) o copia pineada a un commit de la rama `19.0`? Recomendado: pinear a commit (reproducibilidad de build) y documentar el commit hash de cada repo.

---

## Fase 0 — Resguardo del origen `→ Plan §2, §13`

> Antes de tocar nada. El Online sigue siendo la fuente de verdad hasta el corte.

- [ ] Backup completo del Online: **zip dump + filestore** desde la gestión de la base en la cuenta Odoo.
- [ ] Guardar el backup en **almacenamiento externo** (no solo en la PC de Renzo) y verificar que el zip abre.
- [ ] Exportar a CSV/PDF los **reportes históricos** que el cliente quiera conservar fuera de Odoo (ventas, IVA, etc.).
- [ ] 🔗**(externo)** Confirmar con el contador la **retención legal** de comprobantes históricos.
- [ ] Decidir destino del Online tras el corte: **read-only como archivo** o baja. Documentar la decisión.
- [ ] Anotar la versión exacta del origen (**19.0.1.3**) y el inventario de datos (604 productos, 50 contactos) por si hay que reconciliar.

**✅ DoD Fase 0:** existe un backup íntegro y verificado del Online fuera de la plataforma, y está decidido qué pasa con la instancia vieja.

---

## Fase 1 — VPS + Infraestructura Docker `→ Plan §8`

> **Todo en Docker es mandatorio.** El Dockerfile a medida es la pieza clave (resuelve M2Crypto + pyafipws dentro de la imagen).

### 1.1 VPS base (Hostinger)
- [ ] Provisionar VPS. Sizing de arranque: **2 vCPU / 4 GB / 40–60 GB SSD** (holgura: 4 vCPU / 8 GB).
- [ ] Instalar **Docker + Docker Compose**.
- [ ] Hardening básico: usuario no-root, SSH por clave, firewall (solo 80/443/SSH), `fail2ban`.
- [ ] DNS: apuntar el dominio/subdominio del cliente al **VPS donde corre el NPM existente** (es quien termina el SSL).
- [ ] Identificar y documentar el **nombre de la red Docker del NPM existente** (`docker network ls`) — es la red a la que se conectará el contenedor `odoo`.

### 1.2 Imagen Odoo a medida (`docker/Dockerfile`)
- [ ] Base `FROM odoo:19`.
- [ ] Instalar **dependencias de sistema** ANTES del pip: `swig libssl-dev python3-dev build-essential pkg-config`. `→ Plan §7.3`
- [ ] Instalar **dependencias Python** (`requirements.txt`): `pyOpenSSL`, `M2Crypto`, `httplib2>=0.7`, `pysimplesoap~=1.8.22`, `git+https://github.com/filoquin/pyafipws.git@py3k`, `xlrd`. `→ Plan §7.2`
- [ ] Incorporar los repos de addons al `addons_path` (copiados en build o montados como volumen).
- [ ] Verificar que **`wkhtmltopdf`** (versión parcheada) está presente en la imagen final. `→ Plan §8`
- [ ] Build exitoso de la imagen y `M2Crypto`/`pyafipws` importables (`python -c "import M2Crypto, pyafipws"` dentro del contenedor).

### 1.3 Stack de contenedores (`docker/docker-compose.yml`)
> **Sin proxy propio.** En este servidor **ya corre un NGINX Proxy Manager** (el mismo del setup de Banwood). El SSL sale de ahí. El compose de MPRepuestos **NO** levanta su propio NPM: los contenedores se conectan a la **red Docker existente del NPM** para que pueda enrutar y emitir el certificado Let's Encrypt.

- [ ] Servicio **`db`**: PostgreSQL 16 con **volumen persistente**.
- [ ] Servicio **`odoo`**: imagen propia, volúmenes para **filestore** y **`odoo.conf`**, `depends_on: db`.
- [ ] **Red compartida con el NPM existente:** declarar la red del NPM como `external: true` en el compose y conectar el servicio `odoo` a ella (además de una red interna privada `db`↔`odoo`).
- [ ] **NO publicar el puerto 8069 al host** (`ports:`); exponerlo solo **dentro de la red del proxy** (`expose: 8069`). El NPM llega a `odoo:8069` por nombre de servicio dentro de la red compartida.
- [ ] **NO levantar un segundo NPM** ni ocupar 80/443 (ya los tiene el proxy existente).
- [ ] En el **NPM existente**: crear un *Proxy Host* → `odoo` (puerto 8069) con **SSL Let's Encrypt** para el dominio del cliente.
- [ ] Añadir un segundo destino/location en el NPM para **websocket / longpolling** (puerto **8072** gevent), necesario para PoS y chatter. Habilitar *Websockets Support* en el Proxy Host.
- [ ] Confirmar `proxy_mode = True` en `odoo.conf` (coherente con estar detrás del NPM). `→ 1.4`
- [ ] `.env` con secretos fuera de git (`.env.example` versionado, `.env` en `.gitignore`); incluir el **nombre de la red externa del NPM** como variable.

### 1.4 `docker/odoo.conf`
- [ ] `admin_passwd` fuerte.
- [ ] `db_host = db`.
- [ ] `addons_path` con **todos** los repos de la sección 7 del plan.
- [ ] `workers` (con 1 caja: **2–3 + 1 gevent** alcanza).
- [ ] `proxy_mode = True`.
- [ ] `list_db = False` (en producción).
- [ ] Límites de memoria/tiempo (`limit_memory_hard`, `limit_time_cpu`, `limit_time_real`).

### 1.5 Backups automáticos (`scripts/`)
- [ ] `backup.sh`: **`pg_dump`** del contenedor `db` + copia del **volumen filestore**.
- [ ] Envío a **almacenamiento externo** (otra región) con política de **retención**.
- [ ] Orquestar con cron (host o contenedor dedicado).
- [ ] `restore-test.sh`: **prueba periódica de restore** documentada y ejecutada al menos una vez.

**✅ DoD Fase 1:** `docker compose up` levanta db + odoo conectados a la **red del NPM existente** (sin publicar 8069 al host); el NPM enruta el dominio del cliente a `odoo:8069` con **SSL Let's Encrypt** y websocket OK; Odoo accesible por HTTPS; el contenedor odoo importa `M2Crypto` y `pyafipws`; backup corre y un restore de prueba funciona.

---

## Fase 2 — Baseline Community (módulos + config RI) `→ Plan §7, §9 (1–2)`

### 2.1 Instalación de módulos `→ Plan §7.1`
Verificar la **cadena de dependencias** (manifests) `→ Plan §7.1`:
- [ ] **odoo/odoo (CE):** `l10n_ar`, `point_of_sale`, `stock`, `account`, `account_debit_note`.
- [ ] **ingadhoc/odoo-argentina-ce:** `l10n_ar_afipws`, `l10n_ar_afipws_fe`, `l10n_ar_pos_afipws_fe`, `l10n_ar_reports`.
- [ ] **ingadhoc/odoo-argentina:** `l10n_ar_ux` (+ `l10n_ar_tax` solo si se necesitan retenciones).
- [ ] **ingadhoc/account-payment:** `account_payment_group`, `account_internal_transfer`.
- [ ] **ingadhoc/account-financial-tools:** dependencias base ADHOC.
- [ ] **OCA/reporting-engine:** `report_xlsx`.
- [ ] ⚠️ **Caveat de versión** `→ Plan §7.4`: registrar la `version` de manifest de cada `l10n_ar_afipws*` (todavía `18.0.x`). Dejar nota: **NO confiar en producción hasta validar homologación**. Tener listo "Plan B": Renzo parchea si algún módulo falla en 19.

### 2.2 Configuración contable RI `→ Plan §4, §9`
- [ ] Compañía **MPRepuestosPDV**: país Argentina, moneda **ARS**, condición **Responsable Inscripto**.
- [ ] Plan de cuentas + impuestos de **`l10n_ar`** instalados.
- [ ] Impuesto **IVA 21% Ventas** configurado como **tax-included** (precio con IVA incluido). `→ Plan §4 (Precios)`
- [ ] Usuario(s) internos creados (origen tenía 1).

**✅ DoD Fase 2:** instancia Community con todos los módulos del stack instalados sin error, compañía RI configurada y el IVA 21% desglosando correctamente sobre precios con IVA incluido.

---

## Fase 3 — Datos maestros (productos + contactos) `→ Plan §9`

> Orden de carga importa. Stock **NO** se migra. Se valida oversell.

- [ ] **Categorías de producto** y **categorías de PoS (16)** creadas/importadas.
- [ ] Exportar **productos (604)** del Online: CSV nativo o XML-RPC (`data/export/`).
- [ ] Preparar CSV de import (`data/import/`) con campos: nombre, **código de barras**, **precio (IVA incluido)**, **impuesto 21%**, categoría, categoría PoS, tipo **almacenable**.
- [ ] Importar productos en Community y validar conteo (**604**) y muestreo de precios/impuestos.
- [ ] Importar **contactos (50)**: import simple (43 clientes, 2 proveedores + resto). Datos fiscales solo los que ya existan. `→ Plan §4 (Contactos)`
- [ ] **Stock = 0** (no se migra). `→ Plan §9 (6)`
- [ ] **Habilitar venta con stock cero (oversell):** productos almacenables **sin bloqueo por falta de stock**; validar que no haya restricción activa que impida vender. `→ Plan §4 (Stock), §9`
- [ ] Verificar que un producto de prueba se puede **vender con stock 0/negativo** desde el PoS.

**✅ DoD Fase 3:** 604 productos y 50 contactos cargados y verificados; se puede vender un producto con stock cero desde el PoS.

---

## Fase 4 — FE + PoS en homologación `→ Plan §5, §6, §10, §11`

> El corazón del proyecto. Validar **todo** en homologación antes de producción (por el caveat de versión §7.4).

### 4.1 Prerrequisitos ARCA `→ Plan §6.1`
- [ ] 🛠️**(dev)** Generar par de claves + **CSR** con `openssl` (responsabilidad: Renzo). `→ Plan §6.2`
- [ ] 🔗**(externo)** Subir CSR a ARCA → descargar **`.crt`** (Administración de Certificados Digitales).
- [ ] 🔗**(externo)** Vincular servicio **WSFE (wsfev1)** al certificado (Administrador de Relaciones / Computador Fiscal).
- [ ] 🔗**(externo)** Registrar **Punto de Venta electrónico** tipo Web Service (número libre, no colisiona con el preimpreso 1). `→ Plan §6.3`
- [ ] Recibir del contador: `.crt` + `.key` + **número de PtoVta** + ambiente. `→ Plan §6.1 (5)`
- [ ] Para homologación: usar **WSASS** (certificado de testing) + endpoint **WSFEv1 de homologación**. `→ Plan §6.5`
- [ ] Entregar `docs/checklist-contador.md` (extracto §6.1) con anticipación. `→ Plan §12 (riesgo 7)`

### 4.2 Configuración FE en Odoo `→ Plan §5`
- [ ] Cargar certificado de **homologación** en Odoo.
- [ ] Crear **Diario "Ventas Electrónicas (ARCA)"** tipo *Factura Electrónica (WSFEv1)*, atado al PtoVta electrónico. Tipos: **Factura A, Factura B, NC A, NC B**.
- [ ] Crear **Diario "Ventas Internas (no electrónicas)"** (comprobante no fiscal / orden PoS sin FE). `→ Plan §5`
- [ ] Configurar **FE desde el PoS** con `l10n_ar_pos_afipws_fe` (el operador elige facturar ARCA o no). `→ Plan §10.1`

### 4.3 🛠️(dev) Cobro de cuenta corriente en PoS `→ Plan §10.3`
> El nativo (`account_pos_settle_due`) es Enterprise/propietario → descartado. OCA solo llega a 18.0.

- [ ] **Plan A:** migrar **`pos_session_pay_invoice`** (OCA/pos) de 18.0 → 19.0 (APIs + OWL).
- [ ] **Plan A:** migrar su dependencia **`account_cash_invoice`** (OCA/account-payment) de 18.0 → 19.0.
- [ ] Probar **cobro de un saldo/factura de cliente desde la sesión del PoS**.
- [ ] Evaluar si la UX a nivel **sesión** alcanza; si se necesita el botón **"Pagar deuda" en pantalla del cajero** → **Plan B**: desarrollar módulo propio OWL (`mp_pos_settle_due`).
- [ ] Validar el matiz de **venta a crédito** ("pagar después") en CE puro en 19; si no funciona, usar la vía: **facturar la venta a crédito sin cobrarla** y cobrar luego con el módulo migrado. Documentar la decisión. `→ Plan §10.3 (matiz)`
- [ ] (Si corresponde) Preparar contribución de vuelta a OCA de los módulos migrados.

### 4.4 Impresora 3nStar `→ Plan §10.2`
- [ ] Confirmar que la **3nStar RPT001** se trata como **ESC/POS común** (NO controlador fiscal) — compatible con FE.
- [ ] Instalar driver en la **única PC de caja Windows** y dejar la impresora como predeterminada.
- [ ] Imprimir un ticket de prueba desde el PoS vía navegador/SO.
- [ ] 🔗 Pendiente de dato: ¿hay **cajón de dinero**? → si sí, evaluar **IoT Box**. `→ Plan §14`

### 4.5 Plan de pruebas en homologación `→ Plan §11`
- [ ] Probar **conexión al WS** (botón de test de `l10n_ar_afipws`).
- [ ] Emitir **Factura B** de prueba → devuelve **CAE**.
- [ ] Emitir **Factura A** de prueba (con CUIT de prueba) → devuelve **CAE**.
- [ ] Emitir **Nota de Crédito** de prueba (A y B).
- [ ] Validar **impresión del ticket con CAE + QR** en la 3nStar a **80 mm** (requisito ARCA RG 2021). `→ Plan §10.2`
- [ ] Flujo completo desde el **PoS**: venta facturada (ARCA) + venta interna (no ARCA), cobro, **cierre de sesión**, **asiento contable** y **movimiento de stock** generados.
- [ ] Probar **cobro de cuenta corriente por caja** (según vía elegida en 4.3).

**✅ DoD Fase 4:** en homologación se emiten A/B/NC con CAE válido, el ticket sale con CAE+QR en la 3nStar, el ciclo completo de PoS (ambos diarios) cierra correctamente y el cobro de cc por caja funciona.

---

## Fase 5 — Pase a producción `→ Plan §11 (pase a producción), §13`

- [ ] 🔗**(externo)** Obtener certificado y **PtoVta de producción**.
- [ ] Configurar certificado + endpoints **productivos** en Odoo (cambiar de homologación a producción).
- [ ] `list_db = False` confirmado y `admin_passwd` rotado para producción.
- [ ] Hacer el **corte fuera de horario comercial**.
- [ ] Emitir la **primera factura real controlada**.
- [ ] Verificar **numeración correlativa** y registro en **"Mis Comprobantes"** de ARCA.
- [ ] Tener a mano `docs/runbook-produccion.md` (rollback + troubleshooting).
- [ ] ⚠️ Recordar: la caja necesita **internet al facturar** (el offline del PoS no estampa CAE). `→ Plan §12 (riesgo 5)`

**✅ DoD Fase 5:** primera factura electrónica real emitida con CAE, correlativa y visible en ARCA; sistema en producción operando.

---

## Fase 6 — Post go-live (aprendizaje + hardening) `→ Plan §13 (Fase 6)`

- [ ] Afinar contabilidad: **recibos de cc**, **Libro IVA** (`l10n_ar_reports`), cierres.
- [ ] Afinar inventario: rutas, valuación, ajustes a medida que el dueño controla stock.
- [ ] Monitoreo del VPS (recursos, logs, uptime).
- [ ] **Verificación periódica de backups** (restore de prueba calendarizado).
- [ ] Completar documentación: `docs/manual-cajero.md`, `docs/runbook-produccion.md`.
- [ ] Evaluar `l10n_ar_tax` si aparecen **retenciones/percepciones**. `→ Plan §3 (excluido)`

**✅ DoD Fase 6:** operación estable, backups verificados, documentación entregada y contabilidad/inventario afinados.

---

## Datos pendientes de completar (bloqueantes) `→ Plan §14`

> Estos datos **bloquean** principalmente la Fase 4/5. Perseguirlos en paralelo desde el inicio.

- [ ] 🔗 **CUIT** de la empresa.
- [ ] 🔗 **Certificado digital** ARCA (`.crt`) + **clave privada** (`.key`) — generar y tramitar.
- [ ] 🔗 **Número de Punto de Venta** electrónico (definir y registrar en ARCA).
- [ ] 🔗 **Confirmar tipos de comprobante** (A y/o B) con el contador.
- [ ] 🔗 **¿Acceso a Clave Fiscal del cliente para Renzo, o todo vía contador?**
- [ ] 🔗 **¿Hay cajón de dinero** en la caja? (define si conviene IoT Box).
- [x] PC de caja: **una sola con Windows** (confirmado).
- [x] Cobro de cc en PoS: **definido** — migrar OCA `pos_session_pay_invoice` + `account_cash_invoice` 18→19 (Plan A); dev propio como fallback (Plan B).

---

## Registro de riesgos (vigilancia continua) `→ Plan §12`

| # | Riesgo | Mitigación | Estado |
|---|---|---|---|
| 1 | Migración a 19 de ADHOC reciente (manifests 18.0.x) | Validar todo en homologación; Renzo parchea | ⬜ Abierto |
| 2 | Cobro cc en PoS (nativo Enterprise; OCA hasta 18) | Migrar OCA 18→19 (Plan A) + dev propio (Plan B) | ⬜ Abierto |
| 3 | "Factura A a consumidor final" no es válido | Confirmar con contador; sistema soporta A y B | ⬜ Abierto |
| 4 | Encuadre fiscal de ventas no-ARCA | Definir con el contador | ⬜ Abierto |
| 5 | FE necesita CAE online | La caja debe tener internet al facturar | ⬜ Abierto |
| 6 | M2Crypto puede fallar al compilar | Deps de sistema antes del pip (§7.3) en el Dockerfile | ⬜ Abierto |
| 7 | Certificado/PtoVta dependen del contador | Entregar checklist §6.1 con anticipación | ⬜ Abierto |

---

## Referencias rápidas

- **Plan completo:** [`plan-migracion-mprepuestos-odoo19.md`](./plan-migracion-mprepuestos-odoo19.md)
- **Repos de addons (todos rama `19.0`):** `odoo/odoo`, `ingadhoc/odoo-argentina-ce`, `ingadhoc/odoo-argentina`, `ingadhoc/account-payment`, `ingadhoc/account-financial-tools`, `OCA/reporting-engine`, `OCA/pos`, `OCA/account-payment`
- **Fork pyafipws:** `git+https://github.com/filoquin/pyafipws.git@py3k`
- **División de responsabilidades:** ver `→ Plan §6.2` (Renzo = partner técnico; contador = trámites ARCA + encuadre fiscal)
