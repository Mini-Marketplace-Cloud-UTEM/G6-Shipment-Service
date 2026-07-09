# Justificación y Método de Cálculo de Tarifas de Envío (Grupo 6)

Para el cálculo del valor de envío (tarifa de despacho) que retornamos al Checkout (G4) en el endpoint /api/v1/shipments/quotes, hemos diseñado un **Pricing Engine** o motor de tarifas dinámico.

Este motor fue diseñado para resolver dos grandes problemas logísticos reales:
1. **Cobro por peso volumétrico:** Los paquetes grandes pero livianos ocupan espacio en el camión, por lo que se debe cobrar por volumen si este es mayor al peso real.
2. **Despacho Multi-Origen:** Los productos de una misma orden pueden salir desde diferentes Centros de Distribución (Norte, Centro, Sur).

---

## 1. Peso Facturable según Talla (Billable Weight)

Para simplificar la integración con otros grupos, la API ya no requiere dimensiones físicas ni peso real. En su lugar, recibe la **Talla** del paquete (XS, S, M, L, XL, XXL) y nuestro motor la traduce internamente a un "Peso Facturable Equivalente" en kilogramos.

- **Talla XS:** 1 Kg
- **Talla S:** 2 Kg
- **Talla M:** 5 Kg
- **Talla L:** 10 Kg
- **Talla XL:** 20 Kg
- **Talla XXL:** 40 Kg

---

## 2. Zonificación de Destinos y Orígenes

Hemos categorizado las ciudades de Chile en cinco grandes macro-zonas de destino y cruzamos el centro de distribución de origen logístico (NORTE, CENTRO, SUR) con la ciudad del cliente para determinar el tipo de tarifa a aplicar.

### Distribución de Ciudades por Macro-Zona de Destino
- **NORTE:** Arica, Iquique, Antofagasta
- **CENTRO_NORTE:** Copiapó, La Serena, Coquimbo
- **CENTRO:** Santiago, Valparaíso, Rancagua
- **CENTRO_SUR:** Talca, Chillán, Concepción
- **SUR:** Temuco, Valdivia, Puerto Montt, Punta Arenas

### Matriz de Cruce (Origen vs Destino)

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
