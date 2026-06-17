# Contrato de Integración - Grupo 8 (Pagos y Notificaciones)

## Objetivo
Ajuste de plantillas de correo electrónico para notificar entregas parciales.

## Acción
Procesar los nuevos campos en los eventos Pub/Sub del tópico `shipment-events`.

## Nuevos campos en el JSON
- `package_index` (int): Índice del paquete dentro de la orden.
- `total_packages` (int): Total de paquetes asociados a la orden.

## Impacto
Si el consumidor recibe un evento de entrega con `"package_index": 1, "total_packages": 2`, el sistema de correos debe adaptar su plantilla para informar al usuario final que se trata de una **entrega parcial** y que el resto de su pedido sigue en camino.
