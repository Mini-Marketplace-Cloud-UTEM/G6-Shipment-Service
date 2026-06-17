# Contrato de Integración API G6 - Grupo 7 (Reportería y Métricas)

Este documento detalla los datos que el Grupo 6 (Despacho) provee para la ingesta de analíticas logísticas por parte del Grupo 7.

La integración con G7 no es mediante API REST Síncrona, sino mediante la **ingesta de eventos (Pub/Sub) desde el Event Broker**.

## 1. Conexión y Suscripción
G7 debe suscribirse al tópico global Kafka/Supabase denominado `shipment-events`. 

## 2. Esquema de Datos y Eventos
A nivel analítico, G6 ya no opera bajo "Estados Globales", sino a nivel de **Caja Física**. 

## Estructura del Envelope de Eventos
Todos los eventos tienen esta estructura. Se emiten asíncronamente en el tópico global `shipment-events`.

```json
{
  "eventId": "evt-uuid-...",
  "eventType": "ShipmentDelivered",
  "version": "1.0",
  "occurredAt": "2026-06-11T15:00:00Z",
  "producer": "g6-despacho",
  "correlationId": "req-123",
  "payload": {
    "package_index": 1,
    "total_packages": 2,
    "shipment_id": "SHP-1",
    "order_id": "ORD-123",
    "new_status": "DELIVERED"
  }
}
```

### Catálogo de Eventos Publicados por G6
* `ShipmentCreated`: Cuando G5 registra las cajas.
* `ShipmentInTransit`: Cuando la caja física sale de nuestro Centro de Distribución.
* `ShipmentDelivered`: Cuando el courier marca la caja como entregada exitosamente al cliente.
* `ShipmentCancelled`: Cuando se aborta el despacho (generalmente a petición de G5 antes del tránsito).
* `ShipmentFailed`: Cuando hubo un siniestro o no se encontró la dirección de entrega de la caja.
* `ShipmentReturned`: Cuando la caja fallida es devuelta físicamente al CD de origen.


## 3. Impacto Analítico y Dimensiones Clave
El payload de nuestros eventos proporciona nuevas dimensiones analíticas:
* **Métricas a nivel de Caja (`shipment_id`):** Al suscribirse a estos eventos, pueden medir volumetría por caja en lugar de por orden completa.
* **Métricas Geográficas (`origin_cd`):** Podrán generar KPIs y SLAs de tiempo de entrega segmentados por Centro de Distribución (Norte, Centro, Sur).
