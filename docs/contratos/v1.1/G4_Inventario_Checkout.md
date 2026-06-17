# Contrato de Integración API G6 - Grupo 4 (Inventario y Checkout)

Este documento extrae y detalla exclusivamente los puntos de integración que el Grupo 4 debe implementar con el Grupo 6 (Despacho).

## Headers Requeridos
Todos los endpoints exigen los siguientes headers:
- `X-Request-Id`: UUID único de la petición.
- `X-Correlation-Id`: UUID para trazabilidad distribuida.
- `X-Consumer`: Nombre de su servicio (ej: `g4-checkout`, `g1-frontend`).

## Errores Estándar
Todos los errores devuelven un JSON base:
```json
{
  "timestamp": "2026-06-11T14:05:00Z",
  "status": 422,
  "code": "VALIDATION_ERROR",
  "message": "Mensaje de error...",
  "correlationId": "req-123e4567"
}
```


## 1. Responsabilidades
* G4 es responsable de mapear qué producto sale de qué Centro de Distribución (CD).
* Durante el Checkout, antes de cobrar al cliente, deben cotizar las tarifas volumétricas y multi-origen en nuestro sistema.

## 2. Endpoints Disponibles para G4

### 2.1 Cotizar Envío (Tarifa Consolidada)
- **Ruta:** `POST /api/v1/shipments/quotes`
- **Descripción:** Calcula la tarifa consolidada de un conjunto de paquetes basado en orígenes y dimensiones. **No guarda datos en la base de datos de G6.**

**Request Body (JSON):**
Deben enviar los ítems agrupados por caja física.
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

**Respuesta Exitosa (200 OK):**
Recibirán el costo total que deben sumar al ticket final del cliente.
```json
{
  "total_shipping_cost": 10100,
  "currency": "CLP"
}
```
