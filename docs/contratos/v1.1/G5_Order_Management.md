# Contrato de Integración - Grupo 5 (Order Management)

## Objetivo
Actualización en el flujo de creación de despachos (1 Pedido = N Cajas).

## Acción
Actualizar el payload enviado a `POST /api/v1/shipments`.

## Requisito
Al confirmar un pedido pagado, ya no se envía un resumen general. Se debe replicar el arreglo exacto de `packages` que G4 utilizó para cotizar.

## Payload esperado (Entrada)
```json
{
  "order_id": "ORD-123",
  "city": "Santiago",
  "packages": [
    { "origin_cd": "NORTE", "weight_kg": 2.5, "dimensions_cm": { "length": 40, "width": 30, "height": 20 } },
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
