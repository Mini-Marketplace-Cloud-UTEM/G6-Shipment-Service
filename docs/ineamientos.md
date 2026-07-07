# Guía y Lineamiento de Desarrollo

Este documento define las reglas obligatorias y los modelos de datos
compartidos para el **contrato público** que cada grupo expone hacia los
demás (vía REST o eventos). Internamente, cada servicio puede usar el
stack, lenguaje y modelo de base de datos que prefiera — estas reglas
aplican únicamente a lo que un grupo expone hacia afuera.

---

## 1. Identificadores (IDs)

- Los IDs de negocio expuestos en el contrato (`orderId`, `paymentId`,
  `shipmentId`, etc.) usan un código legible con el formato
  `PREFIJO-YYYYMMDD-NNN` (ej. `ORD-20260618-001`), con fecha incluida.
- El ID interno de fila en base de datos (clave primaria) puede ser UUID
  u otro formato; no tiene que coincidir con el ID de negocio expuesto.

## 2. Dinero

- **Actualizado 2026-06-28, por requerimiento del evaluador de la
  asignatura:** todo monto se expresa como **entero de 64 bits**
  (`integer` / `format: int64`, conocido como `long` en Java/C#/etc.).
  **Sigue siendo entero — nunca `number`/`float`/`double`.** Lo único que
  cambia es el ancho (antes 32 bits, ahora 64) para evitar overflow en
  montos grandes. Todos los grupos deben migrar su contrato y su código
  a este ancho.
- La moneda es siempre `CLP` — el enum permitido es `[CLP]`, sin otras
  monedas.
- Ver el esquema `Money` en `shared/components.yaml` para la forma
  exacta (`{ amount: integer (int64), currency: "CLP" }`).

## 3. Forma de error

- Forma estándar: `{ code, message, details?, correlationId? }` (versión
  corta, sin `timestamp`/`status`). Ver esquema `Error` en
  `shared/components.yaml`.
- El campo se llama **`code`**, nunca `error`.
- `details` es un **arreglo de `{field, message}`**, nunca un objeto
  libre. Para errores que no son de validación de formulario (ej.
  `INSUFFICIENT_STOCK`), usar una entrada con el campo relevante como
  `field` y el detalle en `message`
  (ej. `{field: "quantity", message: "Disponible: 1, solicitado: 3"}`).

## 4. Naming

- El contrato público (lo que un servicio expone a los demás) va siempre
  en **camelCase**, sin excepción — se exige en el contrato externo de
  cada servicio, no se delega la traducción únicamente al BFF.
- La base de datos interna de cada servicio puede seguir el casing que
  prefiera; esto aplica solo a los campos expuestos en el contrato REST
  o en los eventos publicados.

## 5. Enums

- Siempre `UPPER_SNAKE_CASE` (ej. `PENDING`, `IN_TRANSIT`, `DELIVERED`).

## 6. Paginación

- Forma estándar:
  ```json
  { "data": [...], "pagination": { "page": 1, "pageSize": 20, "total": 0, "totalPages": 0, "hasNext": false, "hasPrev": false } }
  ```
- Ver esquema `Pagination` en `shared/components.yaml`.

## 7. Fechas

- Formato ISO 8601 en UTC (ej. `2026-06-18T14:30:00Z`).

## 8. Eventos (Pub/Sub)

- Tecnología del curso: "Contratos JSON Pub/Sub".
- Sobre estándar: ver esquema `EventEnvelope` en `shared/components.yaml`
  (`eventId, eventType, version, occurredAt, producer, correlationId,
  payload`).
- El `payload` va en camelCase, igual que el resto del contrato público.

## 9. Despliegue

- Todo microservicio se empaqueta y despliega con **Docker** (tecnología
  obligatoria del curso).
- Motivo: con 8 equipos en distintos stacks, Docker es el denominador
  común para que la plataforma de despliegue (Render u otra) levante a
  todos de la misma forma, sin depender de detección automática por
  lenguaje.
- Cada grupo adapta el `Dockerfile` según su stack (Python/FastAPI,
  Node/Express, etc.).

## 10. Versionado de contratos

- Todo cambio que altere la forma de una respuesta (ej. de objeto a
  arreglo) o quite un campo requerido **debe** subir la versión en la URL
  (`/v1/` → `/v2/`), nunca cambiar el contrato en silencio bajo la misma
  versión.
- Todo cambio se sube como Pull Request a este repo
  (`marketplace-contracts`), no se anuncia solo de palabra ni se deja
  solo en un documento de Office.

## 11. Fuente de verdad

- El único contrato válido es el `openapi.yaml` (o `events.yaml`) dentro
  de `services/group-N-x/` en este repo.
- PDF, DOCX, o copias en el repo de servicio propio **no son contrato**
  — son documentación de diseño interna y pueden quedar desactualizadas.

## 12. Orquestación del checkout

- El servicio de **Carro/Checkout** orquesta el flujo completo de
  compra: valida stock, reserva inventario, y dispara la creación del
  pedido en el servicio de Pedidos. El BFF no reimplementa esta
  orquestación — consume el endpoint de checkout expuesto por ese
  servicio.

---

## 13. Modelos canónicos compartidos

Define el nombre y forma que cada entidad de negocio debe tener en el
**contrato público**, para que dos servicios que hablan de "un pedido"
se refieran exactamente a los mismos campos.

### User (dominio: Auth)

| Campo | Tipo |
|---|---|
| `id` | uuid |
| `name` | string |
| `email` | string (email) |
| `phone` | string |
| `avatarUrl` | string (uri), nullable |
| `roles` | array de `guest/customer/seller/admin` |
| `active` | boolean |
| `createdAt`/`updatedAt` | date-time |

### Product (dominio: Catálogo)

| Campo | Tipo |
|---|---|
| `id` | uuid |
| `name` | string |
| `description` | string |
| `price` | `Money` (int64 + CLP) |
| `stock` | integer |
| `categoryId` / `categoryName` | uuid / string |
| `sku` | string |
| `status` | `ACTIVE/INACTIVE/DELETED` |
| `images` | array de uri |

### Category (dominio: Catálogo)

| Campo | Tipo |
|---|---|
| `id` | uuid |
| `name` | string |
| `slug` | string |
| `parentId` | uuid, nullable |
| `children` | array de `Category` |

### Cart / CartItem (dominio: Carro/Checkout)

| Campo | Tipo |
|---|---|
| `cartId` | string de negocio |
| `userId` | uuid |
| `status` | `ACTIVE/COMPLETED/CLOSED` |
| `items[]` | array de `CartItem` |
| `totalAmount` | `Money` |
| `createdAt`/`updatedAt` | date-time |

`CartItem`: `itemId, cartId, productId, name, quantity, unitPrice
(Money), subTotal (Money)`.

### Order / OrderItem (dominio: Pedidos)

| Campo | Tipo |
|---|---|
| `orderId` | string `ORD-YYYYMMDD-NNN` |
| `userId` | uuid |
| `status` | enum (ver tabla de mapeo de estados) |
| `items[]` | array de `OrderItem` |
| `totalAmount`, `subtotal`, `shippingCost` | `Money` (int64, CLP) |
| `shippingAddress` | objeto (street/city/region/country/postalCode) |
| `createdAt`/`updatedAt` | date-time |

### Payment (dominio: Pagos)

| Campo | Tipo |
|---|---|
| `paymentId` | string `PAY-...` |
| `orderId` | string `ORD-YYYYMMDD-NNN` |
| `userId` | uuid |
| `amount` | `Money` |
| `method` | `CARD/TRANSFER` |
| `status` | `PENDING/APPROVED/REJECTED/CANCELLED` |
| `idempotencyKey` | uuid |

### Shipment (dominio: Despacho)

| Campo | Tipo |
|---|---|
| `shipmentId` | string `SHP-...` |
| `orderId` | string |
| `customerName`, `address`, `city` | string |
| `originCd` | `NORTE/CENTRO/SUR` |
| `weightKg`, `volumetricWeight` | number |
| `shippingCost` | `Money` (int64, CLP) |
| `status` | `PENDING/IN_TRANSIT/DELIVERED/CANCELLED/FAILED/RETURNED` |
| `estimatedDelivery` | date-time, nullable |

### Notification (dominio: Pagos/Notificaciones)

| Campo | Tipo |
|---|---|
| `notificationId` | string `NTF-...` |
| `userId` | uuid |
| `eventId` | string |
| `eventType` | `ORDER_CREATED/PAYMENT_APPROVED/PAYMENT_REJECTED/PAYMENT_PENDING/SHIPMENT_DELIVERED/STOCK_REJECTED` |
| `title`, `body` | string |
| `channel` | `EMAIL/DASHBOARD/LOG` |
| `status` | `PENDING/DELIVERED/READ/FAILED` |

### Tabla de equivalencia de estados

Cada dominio tiene su propio vocabulario de estado para "lo que le pasa a
un pedido". Esta tabla define la equivalencia a respetar entre ellos:

| `OrderStatus` (Pedidos) | `Payment.status` (Pagos) | `ShipmentStatus` (Despacho) |
|---|---|---|
| `CREATED` | `PENDING` | — |
| `PAYMENT_PENDING` → `PAID` | `APPROVED` | — |
| `STOCK_RESERVED` → `READY_TO_SHIP` | — | `PENDING` |
| `SHIPPED` | — | `IN_TRANSIT` |
| `DELIVERED` | — | `DELIVERED` |
| `CANCELLED` / `FAILED` | `REJECTED`/`CANCELLED` | `CANCELLED`/`FAILED`/`RETURNED` |

---

## 14. Contratos-mock: cómo no esperar a que todos terminen

**Problema:** un grupo no puede empezar a integrar contra el contrato de
otro si ese otro grupo todavía no tiene su servicio real implementado.

**Solución:** el contrato (`openapi.yaml`) debe declarar **ejemplos
completos (`example:`) en cada respuesta**, y cada grupo debe levantar un
**mock server público** que sirva esos ejemplos como si la
infraestructura real ya existiera — sin necesidad de programar lógica de
negocio ni conectar base de datos todavía.

### Cómo hacerlo (Prism)

```bash
npx @stoplight/prism-cli mock services/group-N-x/openapi.yaml
```

Esto levanta un servidor que responde automáticamente con los `example:`
definidos en el propio YAML — cero código adicional.

### Qué se pide a cada grupo

1. Completar `example:` en cada respuesta de su `openapi.yaml` (datos de
   ejemplo realistas, no placeholders vacíos).
2. Desplegar ese mock en una URL pública (mismo Render/Docker que usarían
   para el servicio real).
3. Publicar esa URL como `servers:` temporal en su propio contrato, o en
   el registro de servicios.
4. Cuando el servicio real esté listo, **se reemplaza solo la URL** —
   el consumidor no debería tener que cambiar nada de su código, porque
   la forma de la respuesta (el contrato) es la misma.
