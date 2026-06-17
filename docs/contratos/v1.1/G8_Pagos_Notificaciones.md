# Contrato de Integración API G6 - Grupo 8 (Pagos y Notificaciones)

Este documento detalla la integración asíncrona que el Grupo 8 debe implementar para recibir notificaciones de estado de despachos desde el Grupo 6.

La integración no se hace mediante llamadas REST al G6. G8 actúa como **consumidor** de nuestros eventos.

## 1. Conexión y Suscripción
G8 debe suscribirse al tópico global Kafka/Supabase denominado `shipment-events`. 

## 2. Esquema de Datos y Eventos

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


## 3. Lógica para Entregas Parciales (Notificaciones al Cliente)

Dado que G6 maneja la logística por cajas independientes físicas, G8 es el responsable de informar adecuadamente al usuario si ha recibido una parte o el total de su pedido.

**¿Cómo identificar Entregas Parciales?**
Cada evento que afecte el estado físico de una caja trae en su `payload` dos variables críticas:
- `package_index`
- `total_packages`

**Regla de Negocio en G8:**
Al recibir un evento `ShipmentDelivered` (o análogos):
1. Si `package_index < total_packages`: G8 dispara una plantilla de email dinámica **"Entrega Parcial"**. Ejemplo: *"Tu caja 1 de 2 ha sido entregada. ¡El resto sigue en camino!"*
2. Si `package_index == total_packages`: G8 evalúa que la orden está completa y envía la plantilla final **"Pedido Completado"**.
