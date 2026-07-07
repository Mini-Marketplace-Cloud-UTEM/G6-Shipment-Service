# Contrato de Integración API G6 - Grupo 1 (Frontend)

Este documento extrae y detalla exclusivamente los puntos de integración que el Grupo 1 (Frontend) debe implementar para consumir los servicios del Grupo 6 (Despacho).

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


## 1. Endpoints Disponibles para G1

### 1.1 Consultar Despachos por Pedido (Tracking General)
Endpoint utilizado para renderizar la vista de estado de un pedido completo.
- **Ruta:** `GET /api/v1/shipments?orderId={id}`
- **Descripción:** Devuelve un arreglo de objetos correspondientes a todas las cajas de un pedido. Esto permite pintar entregas parciales.

**Respuesta Exitosa (200 OK):**
```json
[
  {
    "shipmentId": "SHP-20260611-001",
    "orderId": "ORD-20260611-001",
    "originCd": "CENTRO",
    "status": "DELIVERED",
    "createdAt": "2026-06-11T14:00:00Z",
    "estimatedDelivery": "2026-06-14T18:00:00Z"
  },
  {
    "shipmentId": "SHP-20260611-002",
    "orderId": "ORD-20260611-001",
    "originCd": "NORTE",
    "status": "IN_TRANSIT",
    "createdAt": "2026-06-11T14:00:00Z",
    "estimatedDelivery": "2026-06-15T18:00:00Z"
  }
]
```

### 1.2 Consultar Despacho por ID (Tracking Específico)
- **Ruta:** `GET /api/v1/shipments/{shipmentId}`
- **Descripción:** Retorna el detalle exhaustivo de una caja específica.

**Respuesta Exitosa (200 OK):**
```json
{
  "shipmentId": "SHP-20260611-001",
  "orderId": "ORD-20260611-001",
  "customerName": "María González",
  "address": "Av. Providencia 1234, Depto 56",
  "city": "Santiago",
  "weightKg": 3.2,
  "status": "PENDING",
  "createdAt": "2026-06-11T14:00:00Z",
  "updatedAt": "2026-06-11T16:00:00Z"
}
```

## 2. Lógica de Estados (Nivel Comercial)

G6 solo devuelve estados físicos **Por Caja** (`PENDING`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED`, `FAILED`, `RETURNED`). 
G1 es responsable de leer el **arreglo de cajas** de la consulta `GET ?orderId=` y calcular al vuelo el "Estado Global" para el usuario final:

* `PENDING`: Todas las cajas están pendientes.
* `PARTIALLY_DELIVERED`: Al menos una caja fue entregada, pero el resto sigue en tránsito.
* `DELIVERED`: 100% de las cajas entregadas.
* `HAS_ISSUES`: Al menos un paquete registró estado `FAILED`, `RETURNED` o `CANCELLED`.
