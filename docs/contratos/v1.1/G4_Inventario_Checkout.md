# Contrato de Integración - Grupo 4 (Inventario y Checkout)

## Objetivo
Integración para cotizar tarifas volumétricas y multi-origen antes de procesar el pago.

## Acción
Consumir el nuevo endpoint `POST /api/v1/shipments/quotes`.

## Requisito
Una vez identificado el Centro de Distribución (CD) de cada ítem del carrito, deben enviarnos las dimensiones exactas.

## Payload esperado (Entrada)
```json
{
  "city": "Santiago",
  "address": "Av. Providencia 1234",
  "packages": [
    {
      "origin_cd": "NORTE",
      "weight_kg": 2.5,
      "dimensions_cm": { "length": 40, "width": 30, "height": 20 }
    }
  ]
}
```

## Respuesta de G6
```json
{
  "total_shipping_cost": 6600,
  "currency": "CLP"
}
```
Este valor debe sumarse al total del checkout.
