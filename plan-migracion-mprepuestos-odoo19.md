# Plan de Migración y Puesta en Marcha
## MPRepuestos — Odoo Online 19 (Enterprise/SaaS) → VPS Hostinger (Community 19)

> Documento de planificación. Reúne todo lo definido en las conversaciones de relevamiento + la auditoría de solo lectura de la instancia online + la investigación del stack ADHOC para Odoo 19. Sirve como base de trabajo y como pliego para coordinar con el contador del cliente.
>
> **Fecha:** mayo 2026 · **Versión origen:** Odoo 19.0.1.3 (Online/SaaS) · **Destino:** Odoo 19.0 Community en VPS Hostinger

---

## 1. Objetivo y estrategia

Mover el Odoo Online (que corre Enterprise) a un **VPS propio con Odoo 19 Community**, arrancando con **contabilidad limpia desde cero** y con el objetivo central de habilitar **facturación electrónica contra ARCA (ex-AFIP) desde el Punto de Venta**.

**Estrategia elegida: instalación Community nueva + migración de datos maestros.** No se migra el historial transaccional. Es la opción más limpia y de menor riesgo, habilitada por el hecho de que la contabilidad/inventario nunca se configuraron a mano y no hay personalizaciones de Studio.

El proyecto también se toma como instancia de **aprendizaje**: configurar correctamente contabilidad RI + FE por primera vez, validando en ambiente de homologación antes de producción.

---

## 2. Diagnóstico del origen (auditoría read-only)

| Ítem | Valor |
|---|---|
| Versión | Odoo 19.0.1.3, Online/SaaS (Enterprise) |
| Empresa | MPRepuestosPDV — Argentina — ARS — **Responsable Inscripto** |
| Módulos instalados | 209 (77 Enterprise, casi todos puentes/dependencias) |
| **Studio** | **No instalado** (cero personalizaciones a reescribir) |
| Punto de venta | 1 punto retail ("MPRepuestos Alem"), no restaurante |
| Medios de pago PoS | Efectivo, Tarjeta, Cuenta de cliente |
| Categorías PoS | 16 |
| Usuarios internos | 1 |
| Productos | 604 (sin variantes) |
| Contactos | 50 (43 clientes, 2 proveedores) |
| Facturación electrónica hoy | **No activa** — 0 comprobantes con CAE; diario "Ventas Preimpreso", sin sistema electrónico |
| Historial (se descarta) | 4.179 órdenes PoS · 226 sesiones · 3.761 asientos · 3.987 movimientos de stock |

**Resguardo del origen:** antes del corte se baja un backup completo (zip dump + filestore) desde la gestión de la base en la cuenta de Odoo, y opcionalmente se mantiene el Online en solo lectura un tiempo como archivo histórico. (La retención legal de comprobantes la define el contador.)

---

## 3. Alcance

**Incluido:** Punto de venta, ciclo de ventas, facturación electrónica ARCA (A y B + NC), contabilidad básica de RI, inventario (arranque en cero), migración de **productos** y **contactos**, impresión de ticket/factura.

**Excluido por ahora (a evaluar más adelante):** historial transaccional, retenciones/percepciones (módulo `l10n_ar_tax` disponible si se necesita), conciliación bancaria avanzada, multi-empresa, e-commerce.

---

## 4. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Edición / hosting | Community 19 self-hosted en VPS Hostinger |
| Migración | Datos maestros (productos + contactos). **Sin historial.** |
| Contabilidad | Limpia desde cero, aprender configuración correcta de RI |
| Stock inicial | **Arranque en cero.** El dueño actualiza a medida que vende. **Debe poder vender con stock 0** (oversell habilitado) |
| Precios | **Con IVA incluido** (tax-included). El IVA 21% igual se configura en los productos para que Odoo lo desglose (requisito de ARCA) |
| Contactos cc | Import simple; la cuenta corriente es organizativa. No se exige completar datos fiscales |
| FE | Objetivo central. Comprobantes **A** (a RI con CUIT) y **B** (consumidor final) + sus NC |
| Cobro cuenta corriente | Se cobra **por caja (PoS)**, incluso al abonar saldos de cc |
| Despliegue | **Todo en Docker** (mandatorio, no opcional) |
| Caja física | **Una sola PC con Windows** |

---

## 5. Modelo de los dos diarios (ARCA vs interno)

Los dos tipos de venta recorren **exactamente el mismo ciclo en el PoS**: se completa la venta, se cobra y queda **asentada contablemente y pagada en el sistema**. La única diferencia es si se reporta o no a ARCA. Para llevar la contabilidad separada y saber qué se declaró, se usan dos diarios de venta:

- **Diario "Ventas Electrónicas (ARCA)"** — tipo *Factura Electrónica (Web Service / WSFEv1)*, atado a un Punto de Venta electrónico de ARCA. Emite **CAE**. Tipos habilitados: Factura A, Factura B, NC A, NC B. Desde la caja se factura con el módulo `l10n_ar_pos_afipws_fe` y el ticket sale con **CAE + QR**.
- **Diario "Ventas Internas (no electrónicas)"** — registra la venta completa, cobrada y contabilizada, **sin emitir comprobante fiscal electrónico** a ARCA. En Odoo esto se resuelve con un comprobante no fiscal / orden de PoS sin factura electrónica.

> **Nota fiscal (no es asesoramiento — coordinar con el contador):** un Responsable Inscripto está, en general, obligado a emitir comprobante por sus ventas. El diario "Ventas Internas" queda a criterio del cliente y su contador, que deben definir el encuadre fiscal correcto. Este documento solo describe la capacidad técnica del sistema.

---

## 6. Facturación electrónica ARCA — prerrequisitos y responsabilidades

### 6.1 Qué se necesita (checklist para el contador / Clave Fiscal)

1. **CUIT** de la empresa y su condición (Responsable Inscripto — confirmado).
2. **Certificado digital** para web services:
   - Generar el par de claves + CSR (lo puede preparar el partner con `openssl`).
   - En ARCA (Clave Fiscal) → *Administración de Certificados Digitales* → subir el CSR → descargar el **`.crt`**.
3. **Vincular el certificado al servicio WSFE**:
   - ARCA (Clave Fiscal) → *Administrador de Relaciones de Clave Fiscal* → adherir el servicio **"Facturación Electrónica" (WSFE / wsfev1)** y asociar el certificado (Computador Fiscal).
4. **Registrar el Punto de Venta electrónico**:
   - ARCA (Clave Fiscal) → *Administración de puntos de venta y domicilios* → crear un PtoVta **nuevo** de tipo **"Web Services / Factura Electrónica"** (distinto del preimpreso 1).
5. Pasar al partner: el `.crt` + `.key`, el **número de PtoVta** y el ambiente (homologación / producción).

### 6.2 División de responsabilidades

| Tarea | Responsable |
|---|---|
| Generar CSR / claves (`openssl`) | Partner (Renzo) |
| Subir certificado, vincular WSFE, registrar PtoVta en ARCA | Contador del cliente (o Renzo si le delegan Clave Fiscal) |
| Configurar certificado, diario y FE en Odoo | Partner (Renzo) |
| Definir tipos de comprobante y encuadre fiscal | Contador del cliente |

### 6.3 Número de Punto de Venta

Cualquier número libre (1–99999) que **no colisione** con puntos de venta existentes (el preimpreso era el 1) y que esté registrado en ARCA como tipo Web Service. El mismo número debe configurarse en el diario electrónico de Odoo.

### 6.4 Tipos de comprobante

- **Factura B / NC B** → consumidor final (lo más frecuente en mostrador).
- **Factura A / NC A** → ventas a Responsables Inscriptos (talleres, revendedores) — requiere **CUIT** y condición IVA del comprador.
- ⚠️ **A revisar con el contador:** "Factura A a consumidor final" no es válido en ARCA; a consumidor final corresponde **B**. El sistema queda preparado para ambos.

### 6.5 Ambiente

Primero **homologación** (ambiente de pruebas de ARCA: WSASS para el certificado de testing + endpoint WSFEv1 de homologación). Recién con todo validado se pasa a **producción** (certificado y endpoints productivos).

---

## 7. Stack técnico (módulos + dependencias)

### 7.1 Repositorios y módulos (todos rama `19.0`)

| Repositorio | Módulos que usamos | Para qué |
|---|---|---|
| **odoo/odoo** (Community) | `l10n_ar`, `point_of_sale`, `stock`, `account`, `account_debit_note` | Base: localización AR (plan de cuentas, impuestos, tipos de comprobante), PoS, inventario, contabilidad, notas de débito |
| **ingadhoc/odoo-argentina-ce** | `l10n_ar_afipws`, `l10n_ar_afipws_fe`, **`l10n_ar_pos_afipws_fe`**, `l10n_ar_reports` | Conexión WS ARCA, factura electrónica, **FE desde el PoS**, Libro IVA |
| **ingadhoc/odoo-argentina** | `l10n_ar_ux` (+ `l10n_ar_tax` si se necesitan retenciones) | Mejoras UX contables; retenciones opcionales |
| **ingadhoc/account-payment** | `account_payment_group`, `account_internal_transfer` | Recibos multi-medio (clave para cuenta corriente); dependencia de `l10n_ar_ux` |
| **ingadhoc/account-financial-tools** | (dependencias base ADHOC) | Base requerida por módulos ADHOC |
| **OCA/reporting-engine** | `report_xlsx` | Dependencia de `l10n_ar_reports` |

**Cadena de dependencias confirmada (manifests):**
- `l10n_ar_afipws` → `l10n_ar` · ext. Python: `pyafipws`, `OpenSSL`, `pysimplesoap`
- `l10n_ar_afipws_fe` → `l10n_ar_afipws`, `l10n_ar`, `account_debit_note`
- `l10n_ar_pos_afipws_fe` → `l10n_ar_afipws_fe`, `point_of_sale`
- `l10n_ar_reports` → `l10n_ar`, `report_xlsx` · ext. Python: `xlrd`
- `l10n_ar_ux` → `l10n_ar`, `account_internal_transfer`

### 7.2 Dependencias Python (venv del VPS)

```
pyOpenSSL
M2Crypto
httplib2>=0.7
pysimplesoap~=1.8.22
git+https://github.com/filoquin/pyafipws.git@py3k
xlrd
```

> El fork de `pyafipws` de **filoquin** (rama `py3k`) es el que usa ADHOC para Python 3. Es el que figura en el `requirements.txt` de `odoo-argentina-ce`.

### 7.3 Dependencias de sistema

`M2Crypto` compila contra OpenSSL, así que **antes** del pip install hay que tener:

```
sudo apt install -y swig libssl-dev python3-dev build-essential pkg-config
```

### 7.4 ⚠️ Caveat de versión

Los módulos `l10n_ar_afipws*` están en la rama `19.0` pero su `version` de manifest todavía dice `18.0.x` (solo `l10n_ar_ux` está bumpeado a `19.0.1.9.0`). La portabilidad a 19 es **reciente**. → **Validar obligatoriamente en homologación** (conexión, emisión A/B, NC, CAE, impresión) antes de habilitar producción. Tener a mano un plan B si algún módulo necesita ajuste menor (Renzo puede parchear si hiciera falta).

---

## 8. Infraestructura del VPS (Hostinger)

**Todo se despliega en Docker** (mandatorio). El VPS solo necesita Docker + Docker Compose; cada componente corre en su contenedor.

**Arquitectura de contenedores (Docker Compose):**

- **`db`** — PostgreSQL 16, con volumen persistente para los datos.
- **`odoo`** — imagen propia (Dockerfile a medida) construida sobre la oficial `odoo:19`, que:
  - Agrega los repos ADHOC/OCA al `addons_path` (montados como volumen o copiados en build).
  - Instala las **dependencias Python** de la sección 7 (`pyOpenSSL`, `M2Crypto`, `httplib2`, `pysimplesoap`, el fork `pyafipws` de filoquin, `xlrd`) y las **dependencias de sistema** (`swig`, `libssl-dev`, etc.) en el propio Dockerfile.
  - Monta volúmenes para el **filestore** y para `odoo.conf`.
- **`proxy`** — NGINX Proxy Manager (ya conocido del setup de Banwood) para reverse proxy + SSL Let's Encrypt, con **websocket/longpolling** habilitado (PoS y chatter) y `proxy_mode = True`.

> El Dockerfile a medida es la pieza clave: resuelve el tema de `M2Crypto` (que necesita compilar contra OpenSSL) y el fork de `pyafipws` desde git **dentro de la imagen**, evitando problemas de entorno en el host.

**`odoo.conf` (montado en el contenedor):** `admin_passwd` fuerte, `db_host = db`, `addons_path` con todos los repos, `workers` (con 1 caja, 2–3 + 1 gevent alcanza), `proxy_mode = True`, `list_db = False` en producción, límites de memoria/tiempo.

**`wkhtmltopdf`:** la imagen oficial de Odoo 19 ya trae la versión parcheada correcta para los PDF; verificar que esté presente en la imagen final.

**Backups automáticos:** `pg_dump` del contenedor `db` + copia del volumen del filestore, a almacenamiento externo (otra región), con retención y **prueba periódica de restore**. Se puede orquestar con un contenedor/cron dedicado o cron del host.

**Sizing sugerido:** arranque cómodo 2 vCPU / 4 GB / 40–60 GB SSD; holgura 4 vCPU / 8 GB. La concurrencia (1 caja) es liviana; el cuello será el reporting y el crecimiento futuro.

---

## 9. Migración de datos maestros (Online → Community)

Orden recomendado de carga:

1. **Usuario(s)** y compañía (MPRepuestosPDV, AR, ARS, RI).
2. **Plan de cuentas + impuestos** → vienen con `l10n_ar`; ajustar IVA 21% Ventas (tax-included).
3. **Categorías de producto** y **categorías de PoS** (16).
4. **Productos (604)** → export nativo de Odoo a CSV (o XML-RPC) desde el Online → import en Community. Campos: nombre, **código de barras**, **precio (IVA incluido)**, **impuesto 21%**, categoría, categoría PoS, tipo (almacenable). 
5. **Contactos (50)** → import simple. La cuenta corriente es organizativa; no se completan datos fiscales salvo los que ya estén.
6. **Stock** → **NO** se migra. Arranca en cero; el dueño hace ajustes a medida que controla.

**Configuración para vender con stock cero:** productos como *almacenables* pero **sin bloquear venta** por falta de stock (el PoS permite overselling por defecto; se valida que no haya restricción activa). El stock podrá quedar negativo hasta que se haga el ajuste.

---

## 10. Configuración PoS + FE + impresora

### 10.1 PoS

- Punto de venta **"MPRepuestos Alem"**, retail.
- Medios de pago: **Efectivo**, **Tarjeta**, **Cuenta de cliente** (venta a crédito → incrementa el saldo del cliente).
- FE desde la caja con **`l10n_ar_pos_afipws_fe`**: el operador elige facturar (ARCA) o no, según el caso.

### 10.2 Impresora

- **3nStar RPT001, térmica 80 mm, USB** → es una impresora **ESC/POS común, NO un controlador fiscal**. ✅ Compatible con el esquema de factura electrónica (controlador fiscal y FE son regímenes excluyentes; al ser térmica común, vamos con FE sin conflicto).
- **Integración:** hay **una sola PC de caja con Windows** (confirmado). Se instala el driver de 3nStar en esa PC y se deja la impresora como predeterminada; el PoS de Odoo imprime el ticket/factura vía navegador/SO.
  - Opcional: **IoT Box** de Odoo si más adelante se quiere impresión ESC/POS directa, corte automático y cajón de dinero.
- **Validar** que el ticket de factura electrónica salga **con CAE + QR** (requisito de ARCA desde RG 2021) en el ancho de 80 mm.

### 10.3 Cobro de cuenta corriente desde la caja (resolución)

El cliente cobra los saldos de cuenta corriente **por la caja del PoS**. El módulo nativo que hace esto, `pos_settle_due` / `account_pos_settle_due`, es de **Odoo Enterprise (licencia propietaria OPL-1) → descartado** (no se compran módulos de terceros).

**Resultado de la investigación (mayo 2026):**

| Fuente | ¿Tiene módulo de cc en PoS? | Estado |
|---|---|---|
| Odoo (`account_pos_settle_due`) | Sí | **Propietario / pago** — descartado |
| **ADHOC** (`ingadhoc`) | **No** | No existe repo `ingadhoc/pos`; su único módulo PoS es la FE (`l10n_ar_pos_afipws_fe`) |
| **OCA** (`OCA/pos` + `OCA/account-payment`) | Parcial: `pos_session_pay_invoice` + `account_cash_invoice` (AGPL) | **Solo hasta 18.0** — todavía **NO portados a 19.0** |

**Decisión: lo resolvemos nosotros, reutilizando la base de OCA.**

- **Plan A (recomendado):** **migrar de 18.0 → 19.0** los módulos OCA `pos_session_pay_invoice` (de `OCA/pos`) y su dependencia `account_cash_invoice` (de `OCA/account-payment`). La lógica ya está hecha y probada; es un trabajo acotado de migración a las APIs/OWL de 19, y se puede **contribuir de vuelta a OCA**. Cubre el **cobro de un saldo/factura de cliente desde la sesión del PoS**.
- **Plan B (fallback / mejora):** si la UX a nivel de **sesión** (backend del PoS) no alcanza y se necesita el botón **"Pagar deuda" dentro de la pantalla del cajero** (como Enterprise), desarrollar un **módulo propio** que lo agregue al frontend OWL del PoS.

**Matiz sobre la venta a crédito (pagar después):** los módulos de arriba cubren el *cobro* del saldo, pero la **venta a crédito** desde el frontend (método "Cuenta de cliente / pagar después" que impacta en la cuenta por cobrar) es una capacidad aparte que en Enterprise también aporta `pos_settle_due`. Hay que **validar si funciona en CE puro en 19**; si no, la vía limpia es **facturar la venta a crédito sin cobrarla** (la factura = la cuenta corriente del cliente) y luego cobrarla con el módulo migrado. Esto se define al implementar.

> En resumen: no dependemos de ningún módulo pago; arrancamos migrando lo de OCA (Plan A) y, si hace falta el flujo completo en pantalla del cajero, lo extendemos con desarrollo propio (Plan B).

---

## 11. Plan de pruebas (homologación → producción)

**En homologación (ARCA testing):**
1. Cargar certificado de homologación y configurar el diario electrónico (PtoVta de prueba).
2. Probar conexión al WS (botón de test de `l10n_ar_afipws`).
3. Emitir **Factura B** y **Factura A** de prueba (con CUIT de prueba para la A) → validar que devuelve **CAE**.
4. Emitir **Nota de Crédito** de prueba.
5. Validar la **impresión** del ticket con CAE + QR en la 3nStar.
6. Probar el flujo completo desde el **PoS**: venta facturada (ARCA) y venta interna (no ARCA), cobro, cierre de sesión, asiento contable y movimiento de stock generados.
7. Probar cobro de **cuenta corriente** por caja (según la vía elegida en 10.3).

**Pase a producción:**
1. Cargar certificado y PtoVta **de producción**.
2. Emitir la primera factura real controlada.
3. Verificar numeración correlativa y registro en "Mis Comprobantes" de ARCA.

---

## 12. Riesgos y puntos abiertos

| # | Riesgo / punto abierto | Mitigación |
|---|---|---|
| 1 | Migración a 19 de ADHOC reciente (manifests en 18.0.x) | Validar todo en homologación; Renzo parchea si hace falta |
| 2 | Cobro de cc en PoS: el nativo es Enterprise; OCA solo hasta 18.0 | Migrar `pos_session_pay_invoice` + `account_cash_invoice` de 18→19 (Plan A); desarrollo propio si se necesita el flujo en pantalla del cajero (sección 10.3) |
| 3 | "Factura A a consumidor final" no es válido | Confirmar con contador; sistema soporta A y B |
| 4 | Encuadre fiscal de ventas no-ARCA | Definir con el contador del cliente |
| 5 | FE necesita **CAE online** | La caja debe tener internet al facturar (el offline del PoS no estampa CAE) |
| 6 | M2Crypto puede fallar al compilar | Instalar dependencias de sistema antes del pip (sección 7.3) |
| 7 | Certificado/PtoVta dependen de terceros (contador) | Entregar checklist de la sección 6.1 con anticipación |

---

## 13. Fases y secuencia

- **Fase 0 — Resguardo:** backup completo del Online + decidir destino (read-only/baja). Exportar reportes históricos que se quieran conservar fuera de Odoo.
- **Fase 1 — VPS (todo en Docker):** instalar Docker + Compose en el Hostinger; armar el Dockerfile de Odoo 19 (repos en `addons_path` + dependencias Python/sistema), el `docker-compose` (db + odoo + NGINX Proxy Manager), `odoo.conf`, volúmenes (filestore/conf) y backups. (Sección 8.)
- **Fase 2 — Baseline Community:** instalar `l10n_ar` + módulos ADHOC/OCA de la sección 7; configurar compañía RI, plan de cuentas, impuesto IVA 21% (incluido), medios de pago.
- **Fase 3 — Datos maestros:** importar productos (604) y contactos (50). Stock en cero. Habilitar venta sin stock.
- **Fase 4 — FE + PoS (homologación):** prerrequisitos ARCA (checklist), certificado de homologación, dos diarios, FE desde PoS, impresora. Ejecutar el plan de pruebas (sección 11).
- **Fase 5 — Producción:** certificado y PtoVta productivos, primera factura real, corte fuera de horario comercial.
- **Fase 6 — Post go-live (aprendizaje):** afinar contabilidad (recibos cc, Libro IVA, cierres), inventario (rutas, valuación), monitoreo, verificación de backups, documentación.

---

## 14. Datos pendientes de completar

- [ ] **CUIT** de la empresa.
- [ ] **Certificado digital** de ARCA (.crt) + **clave privada** (.key) — generar y tramitar.
- [ ] **Número de Punto de Venta** electrónico (definir y registrar en ARCA).
- [ ] **Confirmar tipos de comprobante** (A y/o B) con el contador.
- [ ] **¿Acceso a la Clave Fiscal del cliente para Renzo, o todo vía contador?**
- [ ] **¿Hay cajón de dinero** en la caja? (define si conviene IoT Box).
- [x] PC de caja: **una sola con Windows** (confirmado).
- [x] Cobro de cc en PoS: **definido** — migrar OCA `pos_session_pay_invoice` + `account_cash_invoice` de 18→19 (Plan A); desarrollo propio como fallback (sección 10.3).

---

*Documento de planificación — MPRepuestos · Migración Odoo 19 Online → VPS Community 19 con facturación electrónica ARCA.*
