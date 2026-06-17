# Contrato de Integración - Grupo 8 (Pagos y Notificaciones)

## Objetivo
Ajuste de plantillas de correo electrónico y alertas para notificar entregas parciales a los clientes.

## Acción y Responsabilidad
* Deben consumir los eventos del broker (Pub/Sub en el tópico `shipment-events`).
* Procesar los nuevos campos en el payload JSON.

## Nuevos campos en el JSON
- `package_index` (int): Índice del paquete entregado/enviado.
- `total_packages` (int): Total de paquetes asociados a la orden.

## Impacto
Al detectar un evento donde `package_index < total_packages`, deben despachar plantillas de correo **dinámicas** de "Entrega Parcial". 

**Ejemplo de notificación al usuario final:**
> *"Caja 1 de 2 entregada, tu pedido sigue en camino."*
