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

> ⚠️ **ALERTA PARA G5:** Todos los campos del request body son **OBLIGATORIOS**. El campo `dimensionsCm` es un **objeto** con propiedades `length`, `width` y `height` (no un string). Enviar un payload incompleto o malformado resultará en HTTP 422.

**Request Body (JSON):**
```json
{
  "orderId": "ORD-20260618-001",
  "customerName": "María González",
  "address": "Av. Providencia 1234, Depto 56",
  "city": "Santiago",
  "packages": [
    { "originCd": "NORTE", "weightKg": 2.5, "dimensionsCm": { "length": 40, "width": 30, "height": 20 } },
    { "originCd": "CENTRO", "weightKg": 1.0, "dimensionsCm": { "length": 15, "width": 10, "height": 5 } }
  ]
}
```

**Respuesta Exitosa (201 Created):**
Retorna un objeto con la lista de identificadores físicos. **G5 debe guardar este arreglo de IDs en su BD.**
```json
{
  "shipmentIds": [
    "SHP-20260618-001",
    "SHP-20260618-002"
  ]
}
```

### 2.2 Cancelar Despacho (Por Caja)
- **Ruta:** `PATCH /api/v1/shipments/{shipmentId}`
- **Descripción:** Cancela un despacho específico si el pedido es anulado o hay un problema de fraude detectado a posteriori. 
- **Restricción:** Solo puede ejecutarse si la caja está en estado `PENDING`. Si ya está `IN_TRANSIT`, el servidor devolverá `409 Conflict`.

**Request Body (JSON):**
```json
{
  "status": "CANCELLED"
}
```

**Respuesta Exitosa (200 OK):**
```json
{
  "shipmentId": "SHP-20260618-001",
  "orderId": "ORD-20260618-001",
  "status": "CANCELLED",
  "previousStatus": "PENDING",
  "updatedAt": "2026-06-18T15:00:00Z"
}
```
