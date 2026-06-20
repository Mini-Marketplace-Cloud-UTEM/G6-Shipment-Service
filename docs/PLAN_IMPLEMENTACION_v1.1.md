# 📋 Plan de Implementación — G6-Despacho v1.0 → v1.1

> **Autor:** Grupo 6 — Despacho y Logística  
> **Fecha:** 2026-06-20  
> **Estado:** Aprobado — en ejecución  
> **Entrega objetivo:** Mock E2  

---

## 1. Resumen Ejecutivo

El código actual (`app/`) implementa el modelo **v1.0** (envío único por `order_id`, sin cotizador, sin multi-paquete, sin eventos). Toda la documentación (README, LaTeX v1.1, contratos por grupo, guía interna) describe el modelo **v1.1** como si ya estuviera vigente.

**Objetivo:** Llevar el código a v1.1 completo, generar el `openapi.yaml` formal para la org, y cumplir los 6 criterios de la rúbrica del Mock E2.

---

## 2. Decisiones Técnicas Confirmadas

| Decisión | Resolución |
|---|---|
| **Casing público** | `camelCase` en todos los request/response bodies (con alias Pydantic). La BD interna sigue en `snake_case`. |
| **Formato de error** | Se **mantiene** el formato completo de 5 campos: `timestamp`, `status`, `code`, `message`, `correlationId`. Nuestro contrato lo define así y es más robusto que el formato corto de la org. |
| **Base de datos** | **Supabase PostgreSQL** desde ahora. Se elimina SQLite. Variable de entorno `DATABASE_URL`. |
| **Deploy** | Se actualiza el servicio **existente** en Render (`https://g6-despacho.onrender.com`). |
| **Endpoint cancelación** | El `PATCH /{id}` genérico con `status: CANCELLED` cubre la necesidad. No se crea endpoint `/cancel` separado. |
| **Idempotency-Key** | Documentado pero no validado en el mock. Se implementará en la versión real. |

---

## 3. Análisis de Brechas — Código vs. Contrato

### 3.1 Tabla de Gaps Críticos

| Área | v1.0 (Código actual) | v1.1 (Contrato) | Severidad |
|---|---|---|---|
| `order_id` | `UNIQUE` constraint → 1 shipment por order | Permite **N shipments** por order_id | 🔴 CRÍTICO |
| Endpoint `/quotes` | No existe | `POST /api/v1/shipments/quotes` (cotizador volumétrico) | 🔴 CRÍTICO |
| Campos `origin_cd`, `volumetric_weight`, `shipping_cost` | No existen | Obligatorios en v1.1 | 🔴 CRÍTICO |
| `POST /shipments` request | Recibe 1 envío plano | Recibe arreglo de `packages` con dimensiones por caja | 🔴 CRÍTICO |
| `POST /shipments` response | Retorna objeto completo | Retorna `array` de `shipmentId` strings | 🟠 ALTO |
| `GET /shipments?order_id=` | Retorna 1 objeto o 404 | Retorna **array** de objetos (multi-paquete) | 🟠 ALTO |
| Casing de respuestas | `snake_case` | `camelCase` | 🟠 ALTO |
| Tabla `shipment_status_history` | No existe | Requerida para trazabilidad | 🟡 MEDIO |
| Tabla `outbox_events` | No existe | Requerida para patrón Outbox | 🟡 MEDIO |
| Eventos Kafka | No se publican | Mock: inserción en `outbox_events` | 🟡 MEDIO |
| `openapi.yaml` formal | No existe | Obligatorio para carpeta org | 🔴 CRÍTICO |

### 3.2 Lo que SÍ funciona bien en v1.0

- ✅ Máquina de estados (`VALID_TRANSITIONS`) — correcta y completa
- ✅ Headers obligatorios (`X-Request-Id`, `X-Correlation-Id`, `X-Consumer`)
- ✅ Formato de error unificado (`ErrorResponse`)
- ✅ Paginación en listado (`limit`, `offset`, `total`)
- ✅ Health check endpoint
- ✅ Validaciones Pydantic (campos no vacíos, peso > 0)

---

## 4. Cambios por Archivo

### 4.1 `app/database.py` — Migrar a Supabase

```python
# ANTES (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./despachos.db"
engine = create_engine(URL, connect_args={"check_same_thread": False})

# DESPUÉS (Supabase PostgreSQL)
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
engine = create_engine(DATABASE_URL)
```

- Usar variable de entorno `DATABASE_URL` (inyectada en Render)
- Quitar `check_same_thread` (solo era necesario para SQLite)
- Agregar `psycopg2-binary` a `requirements.txt`

---

### 4.2 `app/models.py` — Nuevas Columnas y Tablas

**Tabla `shipments` (modificada):**
| Columna | Cambio |
|---|---|
| `order_id` | **Quitar `unique=True`** → permitir N registros por order |
| `origin_cd` | **NUEVA** — String, NOT NULL, enum `NORTE/CENTRO/SUR` |
| `volumetric_weight` | **NUEVA** — Float, NOT NULL |
| `shipping_cost` | **NUEVA** — Integer, NOT NULL |

**Tabla `shipment_status_history` (NUEVA):**
| Columna | Tipo |
|---|---|
| `id` | Integer, PK, autoincrement |
| `shipment_id` | String, FK → `shipments.shipment_id` |
| `status` | String, NOT NULL |
| `created_at` | DateTime, default NOW() |

**Tabla `outbox_events` (NUEVA):**
| Columna | Tipo |
|---|---|
| `id` | Integer, PK, autoincrement |
| `event_type` | String, NOT NULL |
| `payload` | JSON, NOT NULL |
| `status` | String, default `PENDING` |
| `created_at` | DateTime, default NOW() |

---

### 4.3 `app/schemas.py` — Nuevos Schemas con camelCase

**Schemas nuevos:**
- `DimensionsCm` — `{ length, width, height }` (todos `float > 0`)
- `PackageInput` — `{ originCd, weightKg, dimensionsCm }`
- `QuoteRequest` — `{ city, packages: List[PackageInput] }`
- `QuoteResponse` — `{ totalShippingCost: int, currency: "CLP" }`

**Schemas modificados:**
- `ShipmentCreate` → recibe `{ orderId, customerName, address, city, packages[] }`
- `ShipmentResponse` → agrega `originCd`, `volumetricWeight`, `shippingCost`

**Configuración camelCase:**
```python
class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

Todos los schemas heredan de `CamelModel` para exponer camelCase automáticamente.

---

### 4.4 `app/main.py` — Endpoints Nuevos y Modificados

#### NUEVO: `POST /api/v1/shipments/quotes`
- Recibe `QuoteRequest` → calcula tarifa consolidada
- Implementa Pricing Engine (peso volumétrico + tarifario por zona)
- No persiste en BD
- Retorna `QuoteResponse`

#### REESCRIBIR: `POST /api/v1/shipments`
- Recibe nuevo schema multi-paquete
- Itera cada package → calcula costo individual
- Inserta N registros en `shipments`
- Inserta N registros en `shipment_status_history` (PENDING)
- Inserta N eventos `ShipmentCreated` en `outbox_events`
  > **⚠️ OJO:** El JSON guardado en `outbox_events.payload` debe cumplir el formato **Envelope** completo del contrato: `eventId`, `eventType`, `version`, `occurredAt`, `producer`, `correlationId`, y el `payload` interno con `packageIndex`, `totalPackages`, `shipmentId`, `orderId`, `newStatus`.
- **Quitar** validación de `order_id` duplicado
- Retorna `List[str]` (array de shipment_ids)

#### MODIFICAR: `GET /api/v1/shipments?order_id=`
- Cambiar `.first()` → `.all()`
- Retornar **array** de todos los shipments del order
- **Estandarizar respuesta:** Retornar el esquema completo `ShipmentResponse` (con todos sus campos: `customerName`, `address`, `weightKg`, `originCd`, `shippingCost`, etc.) para que el "molde" coincida exactamente con la búsqueda por `shipment_id`

#### MODIFICAR: `GET /api/v1/shipments/{shipment_id}`
- Agregar `originCd`, `volumetricWeight`, `shippingCost` al response

#### MODIFICAR: `PATCH /api/v1/shipments/{shipment_id}`
- Agregar insert a `shipment_status_history`
- Agregar insert a `outbox_events` con evento correspondiente

#### MODIFICAR: `GET /api/v1/health`
- Cambiar `version` a `"1.1.0"`

#### NUEVO: `GET /api/v1/shipments/{shipment_id}/history`
- Retorna línea de tiempo inmutable desde `shipment_status_history`

---

### 4.5 Pricing Engine — Lógica de Cotización

```
Peso Volumétrico = (Largo × Ancho × Alto) / 4000
Peso Facturable  = max(Peso Físico, Peso Volumétrico)

Tarifario:
  Misma Zona    → Base $3.000 + ($500  × Kg Facturable)
  Zona Adyacente → Base $5.000 + ($800  × Kg Facturable)
  Zona Extrema   → Base $8.000 + ($1.200 × Kg Facturable)

Costo Total = Σ (Tarifa por Caja)
```

**Mapa de zonas simplificado:**
| Ciudad Destino | Zona |
|---|---|
| Arica, Iquique, Antofagasta | NORTE |
| Santiago, Valparaíso, Rancagua | CENTRO |
| Concepción, Temuco, Puerto Montt, Punta Arenas | SUR |

**Matriz de distancia:**
| Origen \ Destino | NORTE | CENTRO | SUR |
|---|---|---|---|
| **NORTE** | Misma | Adyacente | Extrema |
| **CENTRO** | Adyacente | Misma | Adyacente |
| **SUR** | Extrema | Adyacente | Misma |

---

### 4.6 `openapi.yaml` — Contrato Formal (NUEVO)

- OpenAPI 3.0.3
- Servidor: `https://g6-despacho.onrender.com/api/v1`
- Referencia `$ref` al `shared/components.yaml` de la org para `Error`
- Define todos los schemas en camelCase
- Documenta 7 endpoints con ejemplos completos
- Incluye headers como parameters reutilizables
- Se ubica en: `openapi.yaml` (raíz del repo)
- Se copia a: `services/group-6-despacho/openapi.yaml` (repo org)

---

### 4.7 `README.md` — Actualización

- Actualizar versión a v1.1.0
- Agregar sección "Modelo de Datos" con diagrama de 3 tablas
- Agregar sección "Lógica de Cotización" resumida
- Agregar instrucciones para configurar `DATABASE_URL`
- Asegurar que **todo lo que dice el README sea lo que el código realmente hace**

---

### 4.8 Colección de Pruebas (Postman) — NUEVA

| # | Test | Endpoint | Validación |
|---|---|---|---|
| 1 | Health Check | `GET /health` | Status 200, version 1.1.0 |
| 2 | Cotizar envío (2 cajas) | `POST /quotes` | `totalShippingCost` > 0 |
| 3 | Cotizar sin packages | `POST /quotes` (vacío) | 422 |
| 4 | Crear despacho multi-origen | `POST /shipments` (2 cajas) | Array de 2 IDs |
| 5 | Crear sin headers | `POST /shipments` (sin X-Request-Id) | 422 |
| 6 | Consultar por orderId | `GET /shipments?order_id=ORD-123` | Array de 2 objetos |
| 7 | Consultar shipment específico | `GET /shipments/{id}` | Incluye `originCd` |
| 8 | Transición PENDING→IN_TRANSIT | `PATCH /shipments/{id}` | Status 200 |
| 9 | Transición inválida | `PATCH /{id}` (PENDING→DELIVERED) | 409 |
| 10 | Historial de estados | `GET /shipments/{id}/history` | Array de eventos |

Ubicación: `tests/postman_collection.json`

---

## 5. Archivos Nuevos y Modificados

| Archivo | Acción | Descripción |
|---|---|---|
| `app/database.py` | MODIFICAR | Migrar a Supabase PostgreSQL |
| `app/models.py` | MODIFICAR | Nuevas columnas + 2 tablas nuevas |
| `app/schemas.py` | REESCRIBIR | Schemas v1.1 con camelCase |
| `app/main.py` | REESCRIBIR | Pricing engine + endpoints v1.1 |
| `openapi.yaml` | NUEVO | Contrato formal OpenAPI 3.0.3 |
| `requirements.txt` | MODIFICAR | Agregar `psycopg2-binary` |
| `README.md` | MODIFICAR | Alinear con código real v1.1 |
| `tests/postman_collection.json` | NUEVO | Colección de pruebas |
| `.env.example` | NUEVO | Template de variables de entorno |
| `despachos.db` | ELIMINAR | Ya no se usa SQLite |

---

## 6. Mapeo contra Rúbrica Mock E2

| Criterio | Peso | Antes → Después | Evidencia |
|---|---|---|---|
| **Mock funcional** | 25% | 🔴 v1.0 parcial → 🟢 v1.1 completo, estable | URL Render con todos los endpoints |
| **Repo y estructura** | 15% | 🟡 README desalineado → 🟢 Alineado | README + openapi.yaml + estructura limpia |
| **Modelo de datos** | 20% | 🔴 1 tabla sin campos v1.1 → 🟢 3 tablas completas | DDL en Supabase + diagrama en README |
| **Pruebas de contrato** | 15% | 🔴 No existen → 🟢 10+ tests | Colección Postman exportada |
| **Alineación inter-grupo** | 15% | 🔴 Sin openapi.yaml → 🟢 YAML publicado en org | `services/group-6-despacho/openapi.yaml` |
| **Avance técnico** | 10% | 🟡 v1.0 funcional → 🟢 v1.1 con pricing engine | Código + deploy real |

---

## 7. Orden de Ejecución

- [x] **Paso 1:** Configurar Supabase — crear proyecto, obtener `DATABASE_URL`
- [x] **Paso 2:** Actualizar `database.py` + `requirements.txt`
- [x] **Paso 3:** Reescribir `models.py` — columnas + tablas nuevas
- [x] **Paso 4:** Reescribir `schemas.py` — schemas v1.1 + camelCase
- [x] **Paso 5:** Reescribir `main.py` — pricing engine + todos los endpoints
- [x] **Paso 6:** Generar `openapi.yaml` — contrato formal
- [x] **Paso 7:** Actualizar `README.md`
- [x] **Paso 8:** Crear colección Postman
- [x] **Paso 9:** Verificar localmente (levantar + probar)
- [ ] **Paso 10:** Deploy a Render (push + verificar URL pública)
- [ ] **Paso 11:** Push `openapi.yaml` al repo de la org

---

## 8. Conexión a Supabase (PostgreSQL)

**Datos de conexión:**

| Parámetro | Valor |
|---|---|
| **Host** | `db.cirrgzafgddejnqtrkdy.supabase.co` |
| **Port** | `5432` |
| **Database** | `postgres` |
| **User** | `postgres` |

**Connection string:**
```
postgresql://postgres:G6.DESPACHO@db.cirrgzafgddejnqtrkdy.supabase.co:5432/postgres
```

### Variables de Entorno

| Variable | Valor | Dónde configurar |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:G6.DESPACHO@db.cirrgzafgddejnqtrkdy.supabase.co:5432/postgres` | Render (Environment) + `.env` local |

---

## 9. Repositorios

| Repositorio | URL | Uso |
|---|---|---|
| **G6-Shipment-Service (org)** | `https://github.com/Mini-Marketplace-Cloud-UTEM/G6-Shipment-Service.git` | Repo principal del servicio — aquí se pushea el código v1.1 |
| **marketplace-contracts (org)** | `https://github.com/Mini-Marketplace-Cloud-UTEM/marketplace-contracts.git` | Aquí se sube `services/group-6-despacho/openapi.yaml` |
| **Render (deploy)** | `https://g6-despacho.onrender.com` | Mock público desplegado |

---

> **Nota:** Este plan queda como registro del proceso de ingeniería. Cualquier cambio post-aprobación se documenta aquí como addendum.
