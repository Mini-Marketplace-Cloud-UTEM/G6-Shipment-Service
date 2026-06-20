# Justificación y Método de Cálculo de Tarifas de Envío (Grupo 6)

Para el cálculo del valor de envío (tarifa de despacho) que retornamos al Checkout (G4) en el endpoint /api/v1/shipments/quotes, hemos diseñado un **Pricing Engine** o motor de tarifas dinámico.

Este motor fue diseñado para resolver dos grandes problemas logísticos reales:
1. **Cobro por peso volumétrico:** Los paquetes grandes pero livianos ocupan espacio en el camión, por lo que se debe cobrar por volumen si este es mayor al peso real.
2. **Despacho Multi-Origen:** Los productos de una misma orden pueden salir desde diferentes Centros de Distribución (Norte, Centro, Sur).

---

## 1. Peso Facturable (Billable Weight)

El peso que se utiliza para calcular el costo **no es siempre el peso físico**. Comparamos el peso físico contra el peso volumétrico y cobramos por el mayor de los dos.

- **Peso Físico (weightKg):** Peso real en kilogramos.
- **Peso Volumétrico:** Calculado a partir de las dimensiones del paquete usando un factor de conversión logístico estándar (división por 4000 cm³/kg).
  
  Peso Volumétrico = (Largo * Ancho * Alto) / 4000

- **Peso Facturable:** MAX(Peso Físico, Peso Volumétrico)

---

## 2. Zonificación de Destinos y Orígenes

Hemos categorizado las ciudades de Chile en cinco grandes macro-zonas de destino (NORTE, CENTRO_NORTE, CENTRO, CENTRO_SUR, SUR) y cruzamos el centro de distribución de origen logístico (NORTE, CENTRO, SUR) con la ciudad del cliente para determinar el tipo de tarifa a aplicar:

| Centro de Origen | Zona de Destino | Tipo de Tarifa |
| :--- | :--- | :--- |
| **NORTE** | NORTE | MISMA |
| **NORTE** | CENTRO_NORTE | ADYACENTE |
| **NORTE** | CENTRO | EXTREMA |
| **NORTE** | CENTRO_SUR | EXTREMA |
| **NORTE** | SUR | EXTREMA |
| **CENTRO** | NORTE | EXTREMA |
| **CENTRO** | CENTRO_NORTE | ADYACENTE |
| **CENTRO** | CENTRO | MISMA |
| **CENTRO** | CENTRO_SUR | ADYACENTE |
| **CENTRO** | SUR | EXTREMA |
| **SUR** | NORTE | EXTREMA |
| **SUR** | CENTRO_NORTE | EXTREMA |
| **SUR** | CENTRO | EXTREMA |
| **SUR** | CENTRO_SUR | ADYACENTE |
| **SUR** | SUR | MISMA |

*Nota: Cualquier ciudad de destino no mapeada o desconocida cae por defecto en la categoría de tarifa EXTREMA.*

---

## 3. Matriz de Costos

Una vez resuelto el tipo de tarifa (MISMA, ADYACENTE, EXTREMA), aplicamos un costo base fijo por el servicio de recolección y logística, sumado a un valor por cada kilogramo del *Peso Facturable*.

| Tipo de Tarifa | Costo Base Fijo (CLP) | Costo por Kg Facturable (CLP/Kg) |
| :--- | :--- | :--- |
| **MISMA (Intrazona)** | 3.000 | 500 |
| **ADYACENTE (Interzona corta)** | 5.000 | 800 |
| **EXTREMA (Interzona larga)** | 8.000 | 1.200 |

### Fórmula Final
El cálculo matemático que realiza nuestro backend para cada paquete es:

> **Costo Final = Costo Base Fijo + (Costo por Kg * Peso Facturable)**

En órdenes que contienen múltiples productos desde diferentes orígenes, la API de cotización (/quotes) iterará sobre la lista de paquetes, calculará el costo de cada uno independientemente usando este motor, y retornará la suma total al Checkout.
