# Integración para Cotización de Envíos (Grupo 4)

Este documento explica cómo el **Grupo 4 (Checkout/Carrito)** debe consumir nuestro servicio de despachos para obtener una cotización del costo de envío.

> [!WARNING]  
> **Modo de Operación Dual (Smart Endpoint):** Para evitar bloqueos en la integración (E4) causados por la falta de datos provenientes de otros grupos, hemos habilitado un endpoint inteligente que acepta dos modos de operación. G6 no se hace responsable por la falta de datos volumétricos en la etapa de Checkout; hemos dispuesto esta contingencia para destrabar el flujo.

---

## Endpoint de Cotización

**`POST /api/v1/shipments/quotes`**

Este endpoint calcula el costo estimado del envío. **No crea el despacho**, solo retorna el valor calculado.

### Responsabilidades por Grupo
Para que el cálculo logístico real funcione (volumetría y zonas), dependemos de:
- **G1 (Frontend):** Debe capturar y enviar la ciudad de destino (`city`).
- **G3 (Catálogo):** Debe proveer las dimensiones físicas de cada producto (`dimensionsCm`).
- **G4 (Checkout):** Debe consolidar estos datos y enviarlos a G6.

Dado que G4 actualmente no recibe estos datos de G1 y G3, hemos habilitado el **Modo Parche (Fallback)**.

---

### MODO 1: Oficial (Cálculo Volumétrico Real)

Si G4 cuenta con los datos reales, debe enviar el payload oficial.

**Ejemplo de Request Oficial:**
```json
{
  "city": "Santiago",
  "packages": [
    {
      "originCd": "NORTE",
      "weightKg": 2.5,
      "dimensionsCm": {
        "length": 20,
        "width": 20,
        "height": 20
      }
    }
  ]
}
```

---

### MODO 2: Parche Temporal (Fallback 5%)

Si G4 aún no consolida los datos de G1 y G3, puede enviarnos simplemente el total de la orden. El endpoint detectará esto automáticamente y cobrará un **5% fijo** por concepto de despacho.

**Ejemplo de Request Parche:**
```json
{
  "orderTotalAmount": 15000
}
```
*(El campo es `orderTotalAmount` entero de 64 bits, acorde a la guía de desarrollo).*

---

### Payload de Respuesta (Ambos Modos)

El servicio responderá con el formato estándar de la guía de desarrollo (Money Model):

```json
{
  "totalShippingCost": {
    "amount": 750,
    "currency": "CLP"
  }
}
```

### Errores Posibles

- **`400 Bad Request`**: Si no se envían los datos del Modo 1 ni los datos del Modo 2.
- **`422 Unprocessable Entity`**: Si el tipo de dato es inválido (ej. un string en vez de un int64 para el monto).

---
