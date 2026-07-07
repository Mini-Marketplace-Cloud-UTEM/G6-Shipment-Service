# Contrato de Integración API G6 - Grupo 8 (Pagos y Notificaciones)

Este documento detalla la integración asíncrona que el Grupo 8 debe implementar para recibir notificaciones de estado de despachos desde el Grupo 6.

La integración no se hace mediante llamadas REST al G6. G8 actúa como **consumidor** de nuestros eventos publicados en **Google Cloud Pub/Sub**.

## 1. Conexión y Suscripción
G8 debe suscribirse al tópico de **GCP Pub/Sub** donde G6 publica los eventos de despacho. La publicación se realiza mediante el SDK oficial `google-cloud-pubsub` desde nuestro worker de Outbox.

## 2. Esquema de Datos y Eventos

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


## 3. Lógica para Entregas Parciales (Notificaciones al Cliente)

Dado que G6 maneja la logística por cajas independientes físicas, G8 es el responsable de informar adecuadamente al usuario si ha recibido una parte o el total de su pedido.

**¿Cómo identificar Entregas Parciales?**
Cada evento que afecte el estado físico de una caja trae en su `payload` dos variables críticas:
- `packageIndex`
- `totalPackages`

**Regla de Negocio en G8:**
Al recibir un evento `SHIPMENT_DELIVERED` (o análogos):
1. Si `packageIndex < totalPackages`: G8 dispara una plantilla de email dinámica **"Entrega Parcial"**. Ejemplo: *"Tu caja 1 de 2 ha sido entregada. ¡El resto sigue en camino!"*
2. Si `packageIndex == totalPackages`: G8 evalúa que la orden está completa y envía la plantilla final **"Pedido Completado"**.
