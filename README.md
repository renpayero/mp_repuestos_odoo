# MPRepuestos — Migración a Odoo 19 Community (self-hosted)

> Hoja de ruta ejecutable. Cuando **todos los checkbox estén marcados**, la migración del plan (`plan-migracion-mprepuestos-odoo19.md`) está completa.

---

## 📊 Estado por fase

| Fase | Descripción | Estado |
|------|-------------|--------|
| 0 | Resguardo del origen (export SaaS) | ✅ |
| 1 | VPS + Infraestructura Docker | ✅ |
| 2 | Localización AR + módulos base | 🟨 |
| 3 | Migración de datos maestros | ⬜ |
| 4 | Facturación electrónica ARCA (PoS) | ⬜ |
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

## 🟨 Fase 2 — Localización AR + módulos base

- [ ] Instalar `l10n_ar` (plan de cuentas RI) + `l10n_ar_ux`
- [ ] Instalar `account_payment_pro`, `account_internal_transfer` (account-financial-tools)
- [ ] Configurar compañía: razón social, CUIT, domicilio, RI
- [ ] `report_xlsx` (reporting-engine) para exportaciones
- [ ] ⚠️ FE (`l10n_ar_afipws*`) están `installable=False` en 19.0 → ver Fase 4
- [x] Idioma es_AR por defecto (cargado y activo; usuarios + compañía + default de nuevos partners)

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

## ⬜ Fase 4 — Facturación electrónica ARCA (PoS)

- [ ] Resolver bloqueo de módulos FE (port a 19.0 o forward-port propio)
- [ ] Certificado ARCA (CSR + clave privada) y CUIT homologación
- [ ] Configurar punto de venta + diarios (ARCA vs interno)
- [ ] Pruebas en homologación (WSFEv1): FA/FB/NC
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
- [ ] Cambiar contraseña de `admin` (hoy admin/admin)
- [ ] Hardening del server (firewall, SSH)
- [ ] Cron de backups (`backup.sh` diario + `restore-test.sh` semanal)
- [ ] Backup off-site (rclone a otro destino)

---

## 🧱 Stack técnico (resumen)

- **Odoo 19 Community** (imagen oficial `odoo:19`, personalizada en `docker/Dockerfile`)
- **PostgreSQL 16** en contenedor con volumen persistente
- **Localización AR (ADHOC + OCA)** como submódulos git pineados en `addons/external/`
- **Reverse proxy:** NGINX Proxy Manager existente (`nginx-app-1`, red `nginx_default`)
- **Dominio:** `mp.dakodev.com` · **VPS:** `72.60.156.201`
- **Secretos:** `docker/.env` (gitignored); plantilla en `docker/.env.example`
