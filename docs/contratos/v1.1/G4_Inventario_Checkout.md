# Contrato de Integración - Grupo 4 (Inventario y Checkout)

## Objetivo
Integración para cotizar tarifas volumétricas y multi-origen antes de procesar el pago.

## Responsabilidades
* Son los responsables de mapear qué producto sale de qué Centro de Distribución (CD).
* Deben consumir el nuevo endpoint `POST /api/v1/shipments/quotes` enviando las dimensiones exactas y orígenes.

## Flujo
1. Agrupar ítems por origen.
2. Calcular dimensiones consolidadas por caja a despachar.
3. Llamar a nuestra API de cotización.
4. Recibir nuestro `total_shipping_cost` y sumarlo al ticket final del cliente.

## Payload esperado (Entrada para `/quotes`)
```json
{
  "city": "Santiago",
  "packages": [
    {
      "origin_cd": "NORTE",
      "weight_kg": 2.0,
      "dimensions_cm": { "length": 40, "width": 30, "height": 20 }
    },
    {
      "origin_cd": "CENTRO",
      "weight_kg": 1.0,
      "dimensions_cm": { "length": 15, "width": 10, "height": 5 }
    }
  ]
}
```

## Respuesta de G6
```json
{
  "total_shipping_cost": 10100,
  "currency": "CLP"
}
```
