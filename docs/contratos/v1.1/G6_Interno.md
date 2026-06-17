# Guía de Ingeniería y Arquitectura - Grupo 6 (Despacho)

Este documento es la especificación técnica interna para los desarrolladores Backend del Grupo 6. Aquí se detalla cómo debemos implementar la API de Despachos, nuestra base de datos, y los patrones de resiliencia.

## 1. Responsabilidades de Nuestro Microservicio
Nuestro microservicio opera estrictamente bajo el concepto de **Cajas Físicas**. Nosotros ignoramos qué productos lleva una orden (desacoplamiento total del catálogo e inventario). Nuestro trabajo es:
1. Cotizar envíos basándonos en peso volumétrico y zonas.
2. Registrar la creación de despachos físicos.
3. Transicionar estados físicos (PENDING -> IN_TRANSIT -> DELIVERED).
4. Emitir eventos asíncronos al resto del ecosistema mediante el patrón Outbox.

---

## 2. Modelado de Base de Datos (PostgreSQL / Supabase)

Para soportar el modelo Multi-Origen (1 Pedido = N Cajas), hemos normalizado la base de datos en tres tablas clave.

### 2.1 Tabla Principal: `shipments`
Cada fila representa **una caja física**. El `order_id` ya NO es UNIQUE, porque una orden puede dividirse en varias filas (cajas).

```sql
CREATE TABLE shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    origin_cd TEXT NOT NULL, -- Ej: 'NORTE', 'CENTRO', 'SUR'
    volumetric_weight REAL NOT NULL,
    shipping_cost INTEGER NOT NULL,
    weight_kg REAL NOT NULL CHECK (weight_kg > 0),
    status TEXT NOT NULL DEFAULT 'PENDING',
    CHECK (status IN ('PENDING', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED', 'FAILED', 'RETURNED')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    estimated_delivery TIMESTAMP
);

-- Índices Críticos para Rendimiento de Búsquedas (G1 y G5)
CREATE INDEX idx_shipments_order_id ON shipments(order_id);
CREATE INDEX idx_shipments_status ON shipments(status);
```

### 2.2 Tabla de Historial: `shipment_status_history`
Garantiza trazabilidad inmutable. Cada vez que actualicemos `shipments.status`, debemos insertar una fila aquí en la misma transacción SQL.

```sql
CREATE TABLE shipment_status_history (
    id SERIAL PRIMARY KEY,
    shipment_id TEXT REFERENCES shipments(shipment_id),
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 2.3 Tabla de Resiliencia: `outbox_events`
**Patrón Outbox:** Para evitar que un evento se pierda si Kafka/Event Broker se cae, no publicamos el evento directamente desde el controlador REST.
1. Insertamos en `outbox_events` (status `PENDING`) en la misma transacción SQL que el update de `shipments`.
2. Un Cron Job/Worker lee esta tabla y publica al Broker, marcando como `PUBLISHED`.

```sql
CREATE TABLE outbox_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_outbox_status ON outbox_events(status);
```

---

## 3. Lógica de Cotización (Pricing Engine)
El endpoint `POST /api/v1/shipments/quotes` no guarda en base de datos. Solo itera sobre el arreglo de cajas, aplica la fórmula matemática y retorna el total consolidado.

**Fórmula por Caja:**
1. **Peso Volumétrico:** `(Largo * Ancho * Alto) / 4000`.
2. **Peso Facturable:** `max(Peso Físico, Peso Volumétrico)`.
3. **Cálculo de Tarifa Base:**
   * Misma Zona: Base $3000 + ($500 x Kg Facturable).
   * Zona Adyacente: Base $5000 + ($800 x Kg Facturable).
   * Zona Extrema: Base $8000 + ($1200 x Kg Facturable).
4. **Costo Total (Orden):** `SUM(Tarifa Caja 1 + Tarifa Caja 2 + ... Tarifa Caja N)`.

---

## 4. Máquina de Estados (Nivel Físico)
Nuestro servicio solo evalúa transiciones físicas. **Las transiciones deben validarse en el código antes de hacer el UPDATE**.

| Estado Actual | Transiciones Permitidas | Notas de Validación Interna |
|---------------|-------------------------|-----------------------------|
| `PENDING`     | `IN_TRANSIT`, `CANCELLED` | Solo se puede cancelar si el camión aún no sale. |
| `IN_TRANSIT`  | `DELIVERED`, `FAILED`     | FAILED ocurre por robo o dirección inexistente. |
| `DELIVERED`   | `RETURNED`                | Solo si el cliente inicia un proceso de RMA post-entrega. |
| `CANCELLED`   | Ninguna (Terminal)        | - |
| `FAILED`      | Ninguna (Terminal)        | La caja regresa, pero a nivel logístico el viaje fracasó. |
| `RETURNED`    | Ninguna (Terminal)        | - |

---

## 5. Implementación de Entregas Parciales
Recordatorio de implementación al generar el JSON del evento para G8:
Cuando hagamos el Worker que despacha el Outbox, debemos asegurar que el `payload` incluya `package_index` y `total_packages`.
* ¿De dónde sacamos `total_packages`? Haremos un `COUNT(*)` en `shipments` filtrando por el `order_id` de la caja actual.
* ¿De dónde sacamos `package_index`? Usaremos un simple ranking (ej: `ROW_NUMBER() OVER (ORDER BY created_at)`) para enumerar las cajas de ese `order_id` particular.

---

## 6. Endpoints Internos y Mantenimiento
- **Paginación:** Para `GET /api/v1/shipments?order_id=...`, debemos implementar un array simple. Si en el futuro hacemos GET sin order_id, aplicar limit/offset.
- **Validaciones Críticas:** En el POST, si falta el `origin_cd` o si las medidas son <= 0, retornar inmediatamente `422 Unprocessable Entity`.
