# Contrato de Integración - Grupo 1 (Frontend)

## Objetivo
Manejo visual de entregas parciales y estado global del pedido en la UI de tracking.

## Acción
Ajustar el consumo de los endpoints `GET /api/v1/shipments?order_id={id}` y `GET /api/v1/shipments/{shipment_id}`.

## Impacto y Responsabilidades
* **Array de Cajas:** Al usar los endpoints GET para tracking, deben esperar siempre un array de objetos (cajas), ya que un pedido puede fraccionarse.
* **Estado Global:** Son responsables de iterar sobre el array para calcular el "Estado Global" del pedido de cara al cliente:
    * `PENDING`: Todas las cajas están pendientes.
    * `PARTIALLY_DELIVERED`: Al menos una caja fue entregada, el resto sigue en tránsito.
    * `DELIVERED`: 100% de las cajas entregadas.
    * `HAS_ISSUES`: Al menos un paquete registró fallo o devolución.
* **Progreso Individual:** Deben mostrar visualmente el progreso individual por caja (ej. barras de progreso múltiples), permitiendo al usuario ver el tracking físico independiente de cada parte de su orden.
