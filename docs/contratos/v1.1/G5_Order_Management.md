# Contrato de Integración API G6 - Grupo 5 (Order Management)

Este documento detalla exclusivamente los puntos de integración del Grupo 5 hacia el Grupo 6 (Despacho).

## Headers Requeridos
Todos los endpoints exigen los siguientes headers:
- `X-Request-Id`: UUID único de la petición.
- `X-Correlation-Id`: UUID para trazabilidad distribuida.
- `X-Consumer`: Nombre de su servicio (ej: `g4-checkout`, `g1-frontend`).

## Errores Estándar
Todos los errores devuelven un JSON base:
```json
{
  "timestamp": "2026-06-11T14:05:00Z",
  "status": 422,
  "code": "VALIDATION_ERROR",
  "message": "Mensaje de error...",
  "correlationId": "req-123e4567"
}
```


## 1. Restricciones Críticas de Negocio
* **PROHIBIDO:** Enviar despachos de pedidos que no hayan sido pagados exitosamente.
* **PROHIBIDO:** Enviar resúmenes globales sin el detalle de las cajas físicas (Multi-origen).

## 2. Endpoints Disponibles para G5

### 2.1 Crear Despachos Multi-Origen
- **Ruta:** `POST /api/v1/shipments`
- **Descripción:** Recibe el arreglo que ya fue cotizado en el Checkout (por G4) y genera los registros físicos (1 por caja) en G6.

**Request Body (JSON):**
```json
{
  "order_id": "ORD-123",
  "customer_name": "María González",
  "address": "Av. Providencia 1234, Depto 56",
  "city": "Santiago",
  "packages": [
    { "origin_cd": "NORTE", "weight_kg": 2.5, "dimensions_cm": { "length": 40, "width": 30, "height": 20 } },
    { "origin_cd": "CENTRO", "weight_kg": 1.0, "dimensions_cm": { "length": 15, "width": 10, "height": 5 } }
  ]
}
```

**Respuesta Exitosa (201 Created):**
Retorna un arreglo de identificadores físicos. **G5 debe guardar este arreglo de IDs en su BD.**
```json
[
  "SHP-1",
  "SHP-2"
]
```

### 2.2 Cancelar Despacho (Por Caja)
- **Ruta:** `PATCH /api/v1/shipments/{shipment_id}/cancel`
- **Descripción:** Cancela un despacho específico si el pedido es anulado o hay un problema de fraude detectado a posteriori. 
- **Restricción:** Solo puede ejecutarse si la caja está en estado `PENDING`. Si ya está `IN_TRANSIT`, el servidor devolverá `409 Conflict`.

**Respuesta Exitosa (200 OK):**
```json
{
  "status": "success",
  "message": "Despacho cancelado correctamente."
}
```
