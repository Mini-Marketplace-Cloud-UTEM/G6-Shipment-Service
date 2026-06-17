# Tareas y Arquitectura - Grupo 6 (Interno)

## 1. Modificaciones a la Base de Datos (Supabase / PostgreSQL)

Para soportar el modelo Multi-Origen y asegurar la trazabilidad y resiliencia de eventos, implementamos tres tablas:

### 1.1 Tabla Principal: `shipments`
Eliminamos la restricción `UNIQUE` en `order_id` para permitir 1:N.
```sql
CREATE TABLE shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    origin_cd TEXT NOT NULL, -- 'NORTE', 'CENTRO', 'SUR'
    volumetric_weight REAL NOT NULL,
    shipping_cost INTEGER NOT NULL,
    weight_kg REAL NOT NULL CHECK (weight_kg > 0),
    status TEXT NOT NULL DEFAULT 'PENDING',
    CHECK (status IN ('PENDING', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED', 'FAILED', 'RETURNED')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    estimated_delivery TIMESTAMP
);
```

### 1.2 Tabla de Historial: `shipment_status_history`
Garantiza la trazabilidad (línea de tiempo) inmutable.
```sql
CREATE TABLE shipment_status_history (
    id SERIAL PRIMARY KEY,
    shipment_id TEXT REFERENCES shipments(shipment_id),
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### 1.3 Tabla de Resiliencia: `outbox_events`
Para mitigar caídas del Event Broker mediante patrón Outbox.
```sql
CREATE TABLE outbox_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, PUBLISHED
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

---

## 2. Lógica de Negocio: Tarifa Única Consolidada
El endpoint `/quotes` calcula la suma total para retornar un único cobro:

* **Paso 1:** Peso Facturable = `max(Peso Físico, (Largo * Ancho * Alto)/4000)`.
* **Paso 2:** Tarifario por Macrozona.
  * Misma Zona: Base $3000 + ($500 x Kg Facturable).
  * Zona Adyacente: Base $5000 + ($800 x Kg Facturable).
  * Zona Extrema: Base $8000 + ($1200 x Kg Facturable).
* **Paso 3:** La Ecuación Total Consolidada es la suma del Costo Total de todos los $N$ paquetes.

---

## 3. Máquina de Estados

La máquina de estados a nivel físico se compone de:
* Inicial: `PENDING`
* Tránsito: `IN_TRANSIT`
* Finales Exitosos: `DELIVERED`
* Finales con Error: `CANCELLED`, `FAILED`, `RETURNED`
