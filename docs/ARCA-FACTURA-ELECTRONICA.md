# Facturación Electrónica ARCA — guía operativa y estado

> Guía de trámites + configuración. El contexto técnico del port está en [`CONTEXTO.md`](CONTEXTO.md).
> **Última actualización:** 22 de julio de 2026

---

## 📍 Dónde estamos exactamente

| Paso | Estado |
|---|---|
| Backend FE portado e instalado (`l10n_ar_afipws` + `l10n_ar_afipws_fe`) | ✅ |
| Alias de certificado creado en Odoo (`AFIP WS`, homologación, confirmado) | ✅ |
| CSR generado (certificado en estado `borrador`) | ✅ |
| **Alta del punto de venta en ARCA** | 🔄 **acá estamos** |
| Subir el CSR al portal de ARCA y bajar el `.crt` | ⬜ |
| Autorizar el certificado al web service `wsfe` | ⬜ |
| Cargar el `.crt` en Odoo | ⬜ |
| Crear el diario con el punto de venta | ⬜ |
| Probar conexión (`test_pyafipws_dummy`) | ⬜ |
| Primer CAE en homologación | ⬜ |
| Etapa C: FE desde el PoS | ⬜ |

**Datos de la instancia:** condición fiscal **IVA Responsable Inscripto** (persona física). Entorno actual: **homologación** (`afip.ws.env.type = homologation`).

---

## 1. Los TRES trámites (esto confunde a todo el mundo)

Son **independientes entre sí** y hacen falta los tres. Tener el certificado **no** habilita el punto de venta, y viceversa.

| # | Trámite | Dónde se hace |
|---|---|---|
| 1 | **Certificado digital** — subir el CSR, bajar el `.crt` | Homologación: **WSASS** (`wsass-homo.afip.gob.ar`)<br>Producción: *Administración de Certificados Digitales* |
| 2 | **Autorizar el certificado a usar el WS `wsfe`** | Homologación: WSASS → *"Crear autorización a servicio"*<br>Producción: **Administrador de Relaciones de Clave Fiscal** → *Nueva Relación* → **Facturación Electrónica (wsfe)** |
| 3 | **Alta del punto de venta** | *Administración de puntos de venta y domicilios* |

---

## 2. Punto de venta — investigación completa

### 2.1 Regla formal de ARCA

> *"Los puntos de venta generados mediante los servicios **Comprobantes en línea**, **Facturador Plus** o **Web Services** deberán ser **distintos entre sí**."*
> — [ARCA, Habilitación de puntos de venta](https://www.afip.gob.ar/derechos-de-exportacion-de-servicios/comprobantes-y-facturacion/puntos-de-venta.asp)

Cada punto de venta nace atado a **un sistema de facturación**, y **ese tipo no se puede cambiar nunca**.

**Consecuencia:** si un punto de venta ya en uso es de *Comprobantes en Línea* (el portal manual), **es técnicamente imposible** usarlo desde Odoo por Web Services. ARCA rechaza con:

```
Error 11002 — El punto de venta no se encuentra habilitado a usar en el presente WS.
              Ver método FEParamGetPtosVenta
```

### 2.2 Numeración correlativa

ARCA lleva un contador estricto por cada par **(punto de venta, tipo de comprobante)**. Si el último autorizado fue el 40, el próximo tiene que ser el 41 — **sin saltos ni repetidos**.

Dos sistemas facturando sobre el mismo punto de venta es una **condición de carrera**: el que pregunta primero se lleva el número y el otro recibe:

```
Error 10016 — El número o fecha del comprobante no se corresponde con el próximo a autorizar.
              Consultar método FECompUltimoAutorizado
```

Por eso, **durante la convivencia del sistema viejo con Odoo, hay que usar un punto de venta nuevo**, aunque el existente ya sea de Web Services.

> 💡 **Arrancar de cero no tiene costo:** la numeración es **independiente por punto de venta**. Que la primera factura del punto nuevo sea `FA-A 00003-00000001` es normal y legal — el comprobante se identifica por *punto de venta + número*, no por un correlativo global.

### 2.3 ⚠️ Homologación necesita el punto de venta dado de alta en PRODUCCIÓN

Las fuentes se contradicen y esto **cambia el orden de los pasos**:

| Fuente | Dice |
|---|---|
| FAQ de pyafipws (antigua) | *"En homologación no es necesario declarar puntos de venta"* |
| [Foro pyafipws](https://groups.google.com/g/pyafipws/c/oGQFQqDq8sI) (más reciente) | *"En homologación **ahora solo se puede trabajar con los puntos de venta que están activos** [en producción]"* → error 11002 |
| Idem | `FEParamGetPtosVenta` en homologación devuelve **"Sin Resultados"** |

**Conclusión práctica:** dar de alta el punto de venta **en producción antes de probar en homologación**. No tiene riesgo: un punto de venta habilitado y sin usar **no obliga a nada** — no genera vencimientos ni presentaciones.

### 2.4 Reglas duras que conviene tener presentes

- El número es de **hasta 5 dígitos**
- **Un número usado no se recicla nunca**
- **El tipo de sistema es irreversible** — si te equivocás, hay que dar de baja ese número y crear otro
- Cada punto de venta debe asociarse a un **domicilio declarado** (*Sistema Registral → Registro Tributario → Domicilios*)
- Se pueden tener **varios puntos de venta** por CUIT

### 2.5 Cuántos crear: se recomiendan DOS

| Punto de venta | Uso | Nombre de fantasía sugerido |
|---|---|---|
| ej. `00003` | Odoo — backend (`account.move`) | `Odoo - Administración` |
| ej. `00004` | Odoo — Punto de Venta (PoS) | `Odoo - Mostrador PoS` |

**Por qué dos:**

- **Concurrencia:** si mostrador y administración facturan en el mismo segundo sobre el mismo punto de venta → error 10016. Separados, cada uno tiene su contador y no compiten.
- **Trazabilidad:** de un vistazo se sabe si un comprobante salió del mostrador o de administración.
- **Aislamiento de fallas:** si el PoS queda desalineado, no arrastra a las facturas de administración.
- **Cuesta cero:** se crean en el mismo trámite. Y como **los números no se reciclan ni cambian de tipo**, reservarlos ahora evita otro trámite después.

### 2.6 Procedimiento en el portal

**Requisito previo:** tener el domicilio/local declarado en *Sistema Registral → Registro Tributario → Domicilios*.

1. Entrar a **arca.gob.ar** con **Clave Fiscal**
2. Servicio **"Administración de puntos de venta y domicilios"**
   - Si no aparece en *Mis Servicios*: agregarlo desde el **Administrador de Relaciones de Clave Fiscal** → *Adherir servicio*
3. Clic en el nombre de la empresa / persona
4. **"A/B/M de puntos de venta"** → **"Agregar"**

   > 👀 Esta pantalla **lista cada punto de venta con su sistema asociado** — sirve para verificar de qué tipo es uno existente.

5. Completar:

| Campo | Qué poner |
|---|---|
| **Número del punto de venta** | 5 dígitos, nunca usado antes |
| **Nombre de fantasía** | Libre, solo lo ve ARCA |
| **Sistema** | ⭐ **"RECE para aplicativo y Web Services"** (Responsable Inscripto) |
| **Domicilio** | El local declarado |
| **Dominio asociado** | Opcional |

> El campo **Sistema** según condición fiscal:
> - **Responsable Inscripto** → `RECE para aplicativo y Web Services`
> - Monotributo → `Factura Electrónica – Monotributo – Web Services`
> - Exento en IVA → `Factura Electrónica – Exento en IVA – Web Services`

---

## 3. Flujo del certificado

### Cómo funciona (para entenderlo, no memorizarlo)

```
   ODOO                            ARCA
   ────                            ────
   genera clave privada  ─┐
   (NUNCA sale de Odoo)   │
                          ├─► genera CSR ──────►  firma el CSR
                                                        │
   carga el .crt  ◄──────────────────────────  devuelve certificado .crt
        │
        └─► par completo: clave privada (Odoo) + certificado firmado (ARCA)
```

La **clave privada nunca sale de Odoo**. El CSR y el certificado son públicos.

### Pasos en Odoo

1. **Ajustes → Facturación → AFIP / ARCA Web Services** → poner **Entorno = homologation** → Guardar
2. Botón **"Certificados"** → crear un **alias**:
   - `type`: homologation
   - `common name`: ej. `AFIPWS`
   - país / estado / ciudad
   - **CUIT de la compañía**
   - **`service type`**: `in house` (el certificado es para uso propio; `outsourced` es para un proveedor que factura por vos)
3. **Confirmar** → botón **"Crear pedido de certificado"** → aparece una línea de certificado en estado `borrador`
4. **Obtener el CSR** — dos formas:
   - ✅ **Recomendada:** campo **`request_file`**, tiene ícono de descarga → baja un archivo `.csr`
   - Alternativa: campo **`csr`** (texto que empieza con `-----BEGIN CERTIFICATE REQUEST-----`), **solo visible en modo desarrollador** (`groups="base.group_no_one"`)
5. Subir el CSR al portal de ARCA y bajar el `.crt`
6. **Autorizar el certificado al servicio `wsfe`** (trámite 2 de §1) — sin esto el certificado existe pero no puede facturar
7. En Odoo: botón **"Upload Certificate"** (wizard `action_upload_certificate`) → cargar el `.crt` → Confirmar

> ⚠️ `.gitignore` excluye `*.crt`, `*.key`, `*.pem`. **Las claves y certificados de ARCA nunca se commitean.**

---

## 4. Configuración del diario en Odoo

Un **diario de venta por cada punto de venta**.

**Contabilidad → Configuración → Diarios → Nuevo**

| Campo | Valor |
|---|---|
| Tipo | **Venta** |
| Usar documentos (`l10n_latam_use_documents`) | ✅ |
| **Sistema de PdV de ARCA** (`l10n_ar_afip_pos_system`) | **`Electronic Invoice - Web Service`** |
| **Número de PdV de ARCA** (`l10n_ar_afip_pos_number`) | el número dado de alta (ej. `3`) |

**Cómo funciona internamente:**

```
l10n_ar_afip_pos_system = "RAW_MAW"  ──►  afip_ws = "wsfe"   (mercado interno, WSFEv1)
                          "FEEWS"    ──►  afip_ws = "wsfex"  (exportación)
                          "BFEWS"    ──►  afip_ws = "wsbfe"  (bono fiscal)
```

El mapeo está en `addons/custom/l10n_ar_afipws_fe/models/account_journal.py:32-41`. El código del diario se autocompleta a `"%05i" % l10n_ar_afip_pos_number` (ej. `00003`).

> **Nota:** el diario **`Ventas Preimpreso` (00001, sistema `II_IM`)** lo creó automáticamente la plantilla contable `ar_ri`. **Ese punto de venta 1 no existe necesariamente en ARCA** — es un default de Odoo, no un trámite hecho.

### Botones de diagnóstico (ya portados y funcionando)

En el diario, una vez configurado:

| Método | Qué hace |
|---|---|
| `test_pyafipws_dummy()` | Verifica la infra de ARCA (`AppServerStatus` / `DbServerStatus` / `AuthServerStatus`) |
| `test_pyafipws_point_of_sales()` | ⭐ **Lista los puntos de venta habilitados en ARCA** — confirma el alta desde Odoo |
| `get_pyafipws_last_invoice(document_type)` | Consulta `FECompUltimoAutorizado` — **esto es lo que evita el error 10016** |
| `get_pyafipws_cuit_document_classes()` | Tipos de comprobante autorizados |
| `action_get_connection()` | Fuerza la autenticación WSAA |

---

## 5. Errores frecuentes de ARCA

| Código | Mensaje | Causa / solución |
|---|---|---|
| **10016** | El número o fecha del comprobante no se corresponde con el próximo a autorizar | Numeración desalineada. Consultar `FECompUltimoAutorizado` y usar ese +1. Suele venir de **dos sistemas sobre el mismo punto de venta** |
| **11002** | El punto de venta no se encuentra habilitado a usar en el presente WS | El punto de venta **no está dado de alta**, o **es de otro sistema** (Comprobantes en Línea / Controlador Fiscal) |
| **602** | Sin Resultados — método `FEParamGetPtosVenta` | Normal en **homologación**: ese método no devuelve la lista ahí |
| — | `SOAP Fault: ns1:cms.cert.notAuthorized` | El certificado **no está autorizado al servicio `wsfe`** (falta el trámite 2 de §1) |

---

## 6. Criterios de salida de la Fase 4

### Etapa B — backend (matriz de homologación WSFEv1)

Para cada uno: CAE devuelto, `afip_result == 'A'`, numeración = `get_pyafipws_last_invoice + 1`, QR válido.

- [ ] Factura B a consumidor final
- [ ] Factura A a Responsable Inscripto
- [ ] Nota de Crédito
- [ ] Comprobante exento
- [ ] Con percepciones IIBB
- [ ] Moneda extranjera (RG 5616)
- [ ] Escanear el QR con el validador de ARCA

### Etapa C — PoS

- [ ] Sesión de PoS en homologación → vender → facturar → CAE emitido
- [ ] Ticket muestra **CAE + vencimiento + QR escaneable**
- [ ] Refund → **una sola** Nota de Crédito con `reversed_entry_id` correcto
- [ ] Manejo de error si ARCA se cae en medio de la venta

---

## 7. 🎯 Próximos pasos concretos

1. **Verificar el punto de venta existente** — entrar a *A/B/M de puntos de venta* y ver **de qué sistema es** el que ya está en uso (define si reusarlo era imposible o solo desaconsejado).
2. **Crear los puntos de venta nuevos** con sistema **"RECE para aplicativo y Web Services"**.
3. **Subir el CSR** (ya generado, campo `request_file` del certificado en borrador) al portal de ARCA y bajar el `.crt`.
4. **Autorizar el certificado al WS `wsfe`**.
5. **Cargar el `.crt`** en Odoo con el botón *Upload Certificate*.
6. **Crear el diario** con el punto de venta y correr `test_pyafipws_dummy()` + `test_pyafipws_point_of_sales()`.
7. **Primer CAE** en homologación.

---

## Fuentes

- [ARCA — Habilitación de puntos de venta (oficial)](https://www.afip.gob.ar/derechos-de-exportacion-de-servicios/comprobantes-y-facturacion/puntos-de-venta.asp)
- [ARCA — Factura electrónica (portal oficial)](https://www.afip.gob.ar/fe/)
- [ARCA — Acciones para consumir un Web Service de Factura Electrónica (PDF)](https://www.afip.gob.ar/fe/documentos/AccionesarealizarparaconsumirunWebservicedeFacturaElectr.pdf)
- [ARCA — Manual del desarrollador WSFEv1 (PDF)](https://www.afip.gob.ar/fe/ayuda/documentos/wsfev1-COMPG.pdf)
- [Foro pyafipws — Problemas Puntos de Venta en Homologación](https://groups.google.com/g/pyafipws/c/oGQFQqDq8sI)
- [Cómo crear un Punto de Venta asociado a WebServices en ARCA](https://facturante.ladesk.com/521097-C%C3%B3mo-crear-un-punto-de-venta-asociado-a-WebServices-en-ARCA)
- [Punto de venta AFIP: qué es y cómo configurarlo (2026)](https://yo-facturo.com/blog/punto-de-venta-afip/)
- [Error 10016 en ARCA (AFIP): qué es y cómo solucionarlo](https://emitio.app/blog/error-10016-arca-afip)
- [El punto de venta no se encuentra habilitado para el presente WS (error 11002)](https://tusfacturasapp.tawk.help/article/el-punto-de-venta-no-se-encuentra-habilitado-para-el-presente-ws-en-afip)
- [Documentación oficial Odoo 19 — Localización Argentina](https://www.odoo.com/documentation/19.0/es/applications/finance/fiscal_localizations/argentina.html)
