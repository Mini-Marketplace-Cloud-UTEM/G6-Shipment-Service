# Tareas y Arquitectura - Grupo 6 (Despachos)

## Modificaciones a la Base de Datos (SQL)
- **Modificar tabla `shipments`:** Eliminar el constraint `UNIQUE` de `order_id`. Agregar campos: `origin_cd` (string), `volumetric_weight` (float), `shipping_cost` (int).
- **Crear tabla `shipment_status_history`:** Para trazabilidad del tracking temporal. Campos: `id`, `shipment_id` (FK), `status`, `created_at`.
- **Crear tabla `outbox_events`:** Para implementar el patrón Outbox de Pub/Sub. Campos: `id`, `event_type`, `payload` (JSON), `status` (PENDING/PUBLISHED), `created_at`.

## Nuevo Endpoint: Cotizador de Envíos (`POST /api/v1/shipments/quotes`)
- **Responsabilidad:** Calcular tarifas al vuelo; no guarda registros en la base de datos.
- **Fórmula Matemática:** `Peso Volumétrico (kg) = (Largo_cm * Ancho_cm * Alto_cm) / 4000`. Se cobra usando el mayor valor entre el peso físico y el peso volumétrico.
- **Entrada:** Arreglo de cajas con `city`, `origin_cd`, `weight_kg` y `dimensions_cm`.
- **Salida:** Monto total consolidado en CLP (`total_shipping_cost`).

## Actualización de Endpoints Existentes
- **Creación (`POST /api/v1/shipments`):** Pasa de recibir 1 solo paquete a recibir un arreglo de `packages`. El controlador debe ejecutar un `INSERT` múltiple y devolver un arreglo con los `shipment_id` generados.
- **Consulta por Pedido (`GET /api/v1/shipments?order_id={id}`):** Pasa de devolver un objeto JSON único a devolver un arreglo de objetos de despacho, permitiendo reflejar entregas parciales.

## Eventos al Broker (Pub/Sub)
- **Modificación del Payload:** Todos los eventos emitidos a la cola deben incluir ahora las claves `package_index` (int) y `total_packages` (int) para proveer contexto de fraccionamiento a los consumidores.
