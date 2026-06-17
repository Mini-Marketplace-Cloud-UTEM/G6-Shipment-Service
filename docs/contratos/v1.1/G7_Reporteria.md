# Contrato de Integración - Grupo 7 (Reportería)

## Objetivo
Ingesta de nuevas dimensiones analíticas logísticas.

## Impacto
Al independizar los despachos a nivel de caja física, la tabla `shipments` y los eventos del Broker ahora cuentan con la dimensión `origin_cd` (Norte, Centro, Sur). Esto permite generar reportes de SLA (tiempos de entrega), métricas de éxito y tasas de fallo segmentadas por Centro de Distribución y por paquete individual, superando la limitación de medir únicamente el estado general de la orden de compra.
