# Contrato de Integración API Despachos (G6) - Formato Tallas

Hola equipos (G1, G3, G4, G5),

Para estandarizar y simplificar la logística, la API de Despachos (G6) procesará las cotizaciones y creaciones de despacho basándose en un formato de **Tallas** (`XS`, `S`, `M`, `L`, `XL`, `XXL`) en lugar de dimensiones físicas exactas.

A continuación, detallamos el formato JSON **exacto** que esperamos recibir en nuestros endpoints. 
Les pedimos por favor adaptarse a este formato para que la integración sea transparente y libre de errores.

---

## 1. Cotizar Envío (G4 llamando a G6)
Este endpoint se utiliza en el Checkout para mostrarle el precio de envío al cliente antes de pagar.

**Endpoint:** `POST /api/v1/shipments/quotes`

### Body (JSON) requerido por G6:
```json
{
  "city": "Santiago",
  "packages": [
    {
      "originCd": "NORTE",
      "size": "M"
    },
    {
      "originCd": "CENTRO",
      "size": "XL"
    }
  ]
}
```

*Nota para G4: Deben recolectar las tallas y CDs enviadas por G3, y la ciudad enviada por G1, y unirlas en este arreglo `packages`.*

### Respuesta de G6:
```json
{
  "totalShippingCost": {
    "amount": 12500,
    "currency": "CLP"
  }
}
```

---

## 2. Crear Despacho Oficial (G5 llamando a G6)
Este endpoint se utiliza una vez que la orden ha sido pagada y confirmada, para generar las órdenes de despacho físico.

**Endpoint:** `POST /api/v1/shipments`

### Body (JSON) requerido por G6:
```json
{
  "orderId": "ORD-778899",
  "customerName": "Juan Pérez",
  "address": "Av. Siempreviva 742, Depto 14",
  "city": "Santiago",
  "packages": [
    {
      "originCd": "NORTE",
      "size": "M"
    },
    {
      "originCd": "CENTRO",
      "size": "XL"
    }
  ]
}
```

### Respuesta de G6:
Retornaremos un arreglo con los IDs de seguimiento de los despachos creados (un ID de despacho distinto por cada paquete/CD de origen).
```json
{
  "shipmentIds": [
    "SHP-20260709-001",
    "SHP-20260709-002"
  ]
}
```

---

## Diccionarios Aceptados (Enums)

Para evitar errores HTTP 422 (Unprocessable Entity), asegúrense de respetar mayúsculas y escritura en estos campos:

**Valores válidos para `originCd` (Centro de Distribución):**
* `NORTE`
* `CENTRO`
* `SUR`

**Valores válidos para `size` (Talla del paquete):**
* `XS`
* `S`
* `M`
* `L`
* `XL`
* `XXL`

Cualquier duda con la conexión, ¡nos avisan!
