# Contrato de Integración API G6 - Grupo 7 (Reportería y Métricas)

Este documento detalla los datos que el Grupo 6 (Despacho) provee para la ingesta de analíticas logísticas por parte del Grupo 7.

La integración con G7 es mediante la **ingesta de eventos (Pub/Sub) desde Google Cloud Pub/Sub**.

## 1. Conexión y Suscripción
G7 debe suscribirse al tópico de **GCP Pub/Sub** donde G6 publica los eventos de despacho. La publicación se realiza mediante el SDK oficial `google-cloud-pubsub` desde nuestro worker de Outbox.

## 2. Esquema de Datos y Eventos
A nivel analítico, G6 opera a nivel de **Caja Física** (no orden global).

## Estructura del Envelope de Eventos
Todos los eventos siguen el esquema estándar `EventEnvelope` definido en los lineamientos del curso. Se emiten asíncronamente al tópico GCP.

```json
{
  "eventId": "evt-uuid-...",
  "eventType": "SHIPMENT_DELIVERED",
  "version": "1.1",
  "occurredAt": "2026-06-11T15:00:00Z",
  "producer": "g6-despacho",
  "correlationId": "req-123",
  "payload": {
    "shipmentId": "SHP-20260611-001",
    "orderId": "ORD-20260611-001",
    "customerName": "María González",
    "city": "Santiago",
    "newStatus": "DELIVERED",
    "previousStatus": "IN_TRANSIT",
    "packageIndex": 1,
    "totalPackages": 2
  }
}
```

### Catálogo de Eventos Publicados por G6
* `SHIPMENT_CREATED`: Cuando G5 registra las cajas.
* `SHIPMENT_IN_TRANSIT`: Cuando la caja física sale de nuestro Centro de Distribución.
* `SHIPMENT_DELIVERED`: Cuando el courier marca la caja como entregada exitosamente al cliente.
* `SHIPMENT_CANCELLED`: Cuando se aborta el despacho (generalmente a petición de G5 antes del tránsito).
* `SHIPMENT_FAILED`: Cuando hubo un siniestro o no se encontró la dirección de entrega de la caja.
* `SHIPMENT_RETURNED`: Cuando la caja fallida es devuelta físicamente al CD de origen.

### Payload del Evento `SHIPMENT_CREATED`
Al crear despachos, el payload incluye datos adicionales:
```json
{
  "shipmentId": "SHP-20260611-001",
  "orderId": "ORD-20260611-001",
  "customerName": "María González",
  "address": "Av. Providencia 1234, Depto 56",
  "city": "Santiago",
  "weightKg": 2.5,
  "status": "PENDING",
  "estimatedDelivery": "2026-06-14T14:00:00Z",
  "packageIndex": 1,
  "totalPackages": 2
}
```


## 3. Impacto Analítico y Dimensiones Clave
El payload de nuestros eventos proporciona nuevas dimensiones analíticas:
* **Métricas a nivel de Caja (`shipmentId`):** Al suscribirse a estos eventos, pueden medir volumetría por caja en lugar de por orden completa.
* **Métricas Geográficas (`city`):** Podrán generar KPIs y SLAs de tiempo de entrega segmentados por ciudad de destino.
* **Entregas Parciales (`packageIndex`/`totalPackages`):** Permite calcular tasas de entrega parcial por orden.
