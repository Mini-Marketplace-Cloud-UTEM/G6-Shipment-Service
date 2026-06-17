# Contrato de Integración - Grupo 1 (Frontend)

## Objetivo
Manejo visual de entregas parciales en la UI de tracking.

## Acción
Ajustar el consumo de `GET /api/v1/shipments?order_id={id}` para iterar sobre un arreglo.

## Impacto
Si un pedido consta de 2 cajas, el endpoint devolverá un array con 2 objetos de estado independiente. El Frontend deberá renderizar el tracking permitiendo al usuario visualizar el progreso individual (ej: Caja 1 `DELIVERED`, Caja 2 `IN_TRANSIT`).
