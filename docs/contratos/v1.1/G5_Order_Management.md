# Contrato de Integración - Grupo 5 (Order Management)

## Objetivo
Actualización en el flujo de creación de despachos para soportar la relación (1 Pedido = N Cajas).

## Prohibiciones y Responsabilidades
* 🚫 **PROHIBIDO:** Enviarnos despachos de pedidos sin pagar.
* 🚫 **PROHIBIDO:** Enviarnos resúmenes globales sin detalle de cajas.
* ✅ **ACCIÓN REQUERIDA:** Deben consumir `POST /api/v1/shipments` mandando el **arreglo exacto de cajas** que fue evaluado y cotizado previamente por el Grupo 4.
* ✅ **ACCIÓN REQUERIDA:** Almacenarán el arreglo de `shipment_id` retornados por nuestra API en su base de datos.

## Payload esperado (Entrada)
Añade el `order_id` al arreglo cotizado:
```json
{
  "order_id": "ORD-123",
  "city": "Santiago",
  "packages": [
    { "origin_cd": "NORTE", "weight_kg": 2.0, "dimensions_cm": { "length": 40, "width": 30, "height": 20 } },
    { "origin_cd": "CENTRO", "weight_kg": 1.0, "dimensions_cm": { "length": 15, "width": 10, "height": 5 } }
  ]
}
```

## Respuesta de G6
Retornará una lista de los IDs de despacho generados.
```json
[
  "SHP-1",
  "SHP-2"
]
```
