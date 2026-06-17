# Contrato de Integración - Grupo 7 (Reportería y Métricas)

## Objetivo
Ingesta de nuevas dimensiones analíticas logísticas.

## Impacto y Análisis de Datos
Al independizar los despachos a nivel de caja física, la tabla `shipments` y los eventos del Broker ahora cuentan con la dimensión `origin_cd` (Norte, Centro, Sur).

* **Analytics a Nivel de Caja:** Su ingesta de datos ahora permite Analytics a nivel de Caja (`shipment_id`) en lugar de únicamente a nivel de orden.
* **KPIs:** Utilizarán la dimensión `origin_cd` para generar KPIs de SLAs de tiempo de entrega separados por Centro de Distribución. Esto supera la limitación de medir únicamente el estado general de la orden de compra.
