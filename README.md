# MPRepuestos — Migración a Odoo 19 Community (self-hosted)

> Hoja de ruta ejecutable. Cuando **todos los checkbox estén marcados**, la migración del plan (`plan-migracion-mprepuestos-odoo19.md`) está completa.

## 📚 Documentación

| Documento | Para qué |
|---|---|
| **[`CLAUDE.md`](CLAUDE.md)** | Reglas de trabajo, infra, comandos, gotchas. **Claude Code lo carga solo.** |
| **[`docs/CONTEXTO.md`](docs/CONTEXTO.md)** | Estado completo: decisiones, forward-port, errores resueltos, deuda pendiente |
| **[`docs/ARCA-FACTURA-ELECTRONICA.md`](docs/ARCA-FACTURA-ELECTRONICA.md)** | Guía operativa de ARCA: certificados, puntos de venta, diarios, errores |

**Si venís a retomar el proyecto, leé esos tres en ese orden.**

---

## 📊 Estado por fase

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Resguardo del origen (export SaaS) | ✅ |
| 1 | VPS + Infraestructura Docker | ✅ |
| 2 | Localización AR + módulos base | ✅ |
| 3 | Migración de datos maestros | ⬜ |
| 4 | Facturación electrónica ARCA (PoS) | 🔄 |
| 5 | Operación asistida / paralelo | ⬜ |
| 6 | Go-live + corte | ⬜ |
| - | Hardening / backups / DNS-SSL (transversal) | 🟨 |

---

## ✅ Fase 0 — Resguardo del origen

- [x] Export completo de la base SaaS (ZIP Odoo.sh/Online)
- [x] Descarga de adjuntos/filestore
- [x] Verificación de integridad del backup

---

## ✅ Fase 1 — VPS + Infraestructura Docker

- [x] Docker + Compose instalados en el VPS
- [x] Imagen Odoo 19 CE personalizada (deps AR: M2Crypto, pyafipws, etc.)
- [x] PostgreSQL 16 en contenedor con volumen persistente
- [x] `odoo.conf` con proxy_mode, workers, gevent_port
- [x] Bootstrap idempotente (init DB + admin/admin)
- [x] Repos de terceros como submódulos git pineados
- [x] Stack en la red del NGINX Proxy Manager (`nginx_default`)
- [x] Backups (`backup.sh`) + prueba de restore (`restore-test.sh`)
- [x] DoD verificado: login, deps, wkhtmltopdf, addons disponibles

---

## ✅ Fase 2 — Localización AR + módulos base

### Localización argentina (ADHOC + oficial)
- [x] Instalado `l10n_ar` (oficial CE) + `l10n_ar_ux`, `l10n_ar_tax`, `l10n_ar_bank`, `l10n_ar_purchase(_stock)` (ADHOC 19.0)
- [x] Instalado `l10n_ar_withholding` (retenciones), `account_payment_pro`, `account_internal_transfer`, `account_ux`, `account_background_post`, `l10n_latam_check`
- [x] Configurada compañía: razón social, CUIT (tipo ident. CUIT), domicilio, **Responsable Inscripto**
- [x] **Plan de cuentas `ar_ri`** cargado (313 cuentas, 155 impuestos, 9 diarios, 4 posiciones fiscales); país fiscal = AR
- [x] IVA Ventas/Compras por defecto = 21%; diarios de venta/compra revisados
- [x] `report_xlsx` (reporting-engine) para exportaciones
- [x] Idioma es_AR por defecto (cargado y activo; usuarios + compañía + default de nuevos partners)
- [x] ⚠️ FE (`l10n_ar_afipws*`) venía `installable=False` en 19.0 (ADHOC no liberó el port) → **resuelto con forward-port propio**, ver Fase 4

### Stack contable Community (OCA — repone lo que falta de Enterprise)
CE no trae la app "Contabilidad" (`account_accountant`, EE); solo "Facturación" (`account`). Complementado con OCA:

- [x] `account_financial_report` (Libro Mayor, Balance Sumas y Saldos, Aged Partner, Open Items, Journal Ledger, IVA)
- [x] `account_tax_balance` + `partner_statement` (apoyo IVA + extractos de cuenta)
- [x] `account_reconcile_oca` (+ `account_statement_base`) — conciliación bancaria estilo Enterprise
- [x] `mis_builder` (+ `date_range`) — Balance General / Estado de Resultados configurables

### Módulos de experiencia de usuario (UX)
Copiados de `renzo_odoo` a `addons/custom/` e instalados:

- [x] `web_responsive` (OCA — interfaz tipo Enterprise) `19.0.1.0.2`
- [x] `dako_password` (gestor de contraseñas) `19.0.1.0.0`

---

## ⬜ Fase 3 — Migración de datos maestros

- [ ] Exportar maestros del SaaS (productos, clientes, proveedores)
- [ ] Importar productos (con códigos, precios, impuestos)
- [ ] Importar clientes/proveedores (con CUIT, condición IVA)
- [ ] Importar listas de precios y stock inicial
- [ ] Validar totales y conteos post-importación

---

## 🔄 Fase 4 — Facturación electrónica ARCA (PoS)

> Guía detallada: **[`docs/ARCA-FACTURA-ELECTRONICA.md`](docs/ARCA-FACTURA-ELECTRONICA.md)**

### Forward-port de los módulos (ADHOC 18 → 19)
- [x] Etapa 0 — Vendorizar los 3 módulos FE a `addons/custom/`, sacar `odoo-argentina-ce` del `addons_path`
- [x] Etapa A — `l10n_ar_afipws` instalable y funcionando (`19.0.1.0.0`)
- [x] Etapa B — `l10n_ar_afipws_fe` instalable y funcionando (`19.0.2.0.0`); backend validado en runtime
- [ ] Etapa C — `l10n_ar_pos_afipws_fe` + frontend OWL nuevo (ticket con CAE/vencimiento/QR)
- [ ] Etapa D — Tests + manejo robusto de excepciones

### Trámites y configuración
- [x] Alias de certificado creado en Odoo + CSR generado
- [ ] **Alta de punto de venta en ARCA** (sistema *RECE para aplicativo y Web Services*) ← acá estamos
- [ ] Subir CSR al portal, bajar el `.crt`, autorizarlo al WS `wsfe`
- [ ] Cargar el `.crt` en Odoo
- [ ] Crear diario con el punto de venta y probar conexión
- [ ] Pruebas en homologación (WSFEv1): FA / FB / NC / exento / percepciones / moneda extranjera
- [ ] Pasaje a producción ARCA
- [ ] Capacitación caja / operador PoS

---

## 🟨 Transversal — Hardening / Backups / DNS-SSL

### Acceso y red
- [x] DNS: `mp.dakodev.com` → A → `72.60.156.201` (IP pública del VPS)
- [x] NGINX Proxy Manager: Proxy Host `mp.dakodev.com` → `mprepuestos_odoo:8069` (Websockets ON, `/websocket` → `:8072`)
- [x] SSL Let's Encrypt emitido + Force SSL (HTTPS `200` verificado)
- [x] Puerto 8069 público **cerrado** tras validar HTTPS (acceso solo vía NPM)
- [x] WebSocket del bus en tiempo real: `location /websocket` → `mprepuestos_odoo:8072` en el NPM (handshake `101` verificado; sin esto Odoo muestra el marco amarillo "conexión perdida")

### Seguridad / operación
- [ ] 🚨 Cambiar contraseña de `admin` de Odoo
- [ ] 🚨 SSH: pasar a clave pública (`PasswordAuthentication no`, `PermitRootLogin prohibit-password`)
- [ ] 🚨 Rotar la contraseña de `root` del VPS
- [ ] Activar `ufw` (22/80/443) + instalar `fail2ban`
- [ ] Persistir el bloque `/websocket` en la pestaña **Advanced** del Proxy Host del NPM
- [ ] Cron de backups (`backup.sh` diario + `restore-test.sh` semanal)
- [ ] Backup off-site (rclone a otro destino)

---

## 🧱 Stack técnico (resumen)

- **Odoo 19 Community** (imagen oficial `odoo:19`, personalizada en `docker/Dockerfile`)
- **PostgreSQL 16** en contenedor con volumen persistente
- **Localización AR:** ADHOC `odoo-argentina` + `odoo-argentina-ce` (FE pendiente de port) + `l10n_ar` oficial
- **Contabilidad CE = `account` + OCA:** `account-financial-reporting`, `account-reconcile`, `mis-builder`, `server-ux`
- **Submódulos git pineados** en `addons/external/` (también `account-payment`, `account-financial-tools`, `account-invoicing`, `reporting-engine`)
- **Reverse proxy:** NGINX Proxy Manager existente (`nginx-app-1`, red `nginx_default`)
- **Dominio:** `mp.dakodev.com` · **VPS:** `72.60.156.201`
- **Secretos:** `docker/.env` (gitignored); plantilla en `docker/.env.example`
