# Servicio de Despacho y Logística — Grupo 6 (Marketplace Cloud)

Este repositorio contiene la especificación, documentación técnica y el prototipo funcional (mock) del **Servicio de Despacho y Logística** (Grupo 6) diseñado para el ecosistema del Marketplace Cloud.

El microservicio se encarga de la gestión del ciclo de vida de los envíos (*Shipments*), desde la recepción de la orden de despacho hasta la entrega final al cliente o su devolución, integrando flujos síncronos (REST) y asíncronos (Eventos/Kafka).

---

## 📂 Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

* **[`app/`](app/)**: Código fuente en Python del mock funcional (FastAPI).
  * [`main.py`](app/main.py): Lógica de endpoints, validaciones e inicialización de la API.
  * [`schemas.py`](app/schemas.py): Modelos de datos y schemas Pydantic (alineados con el contrato).
* **[`docs/`](docs/)**: Documentación técnica oficial.
  * [`contratos/`](docs/contratos/): Contrato de la API REST, eventos, C4 y matriz de dependencias.
    * [`v1.0/`](docs/contratos/v1.0/): Versión inicial del contrato.
      * 📑 **[G6_Contrato_API_Despacho.pdf](docs/contratos/v1.0/G6_Contrato_API_Despacho.pdf)**: Documento compilado final.
      * 📄 [G6_Contrato_API_Despacho.tex](docs/contratos/v1.0/G6_Contrato_API_Despacho.tex): Código fuente en LaTeX.
    * [`v1.1/`](docs/contratos/v1.1/): Soporte Multi-Origen y Tarifas Volumétricas.
      * 📑 **[G6_Contrato_API_Despacho_v1.1.pdf](docs/contratos/v1.1/G6_Contrato_API_Despacho_v1.1.pdf)**: Documento compilado final.
      * 📄 [G6_Contrato_API_Despacho_v1.1.tex](docs/contratos/v1.1/G6_Contrato_API_Despacho_v1.1.tex): Código fuente en LaTeX.
      * Archivos Markdown individuales para la integración de cada grupo (`G1_Frontend.md`, `G4_Inventario_Checkout.md`, etc.).
  * [`briefing/`](docs/briefing/): Briefing técnico del servicio.
    * 📑 **[G6_Logistica_Briefing.pdf](docs/briefing/G6_Logistica_Briefing.pdf)**: Documento compilado final.
    * 📄 [G6_Logistica_Briefing.tex](docs/briefing/G6_Logistica_Briefing.tex): Código fuente en LaTeX.
* **[`documentacion_extra_anexos/`](documentacion_extra_anexos/)**: Documentos de trabajo del grupo e insumos de revisión docente (anteriormente `documentos_u`).
* **[`Dockerfile`](Dockerfile)**: Archivo de configuración para la contenedorización del servicio.

---

## 🛠️ Stack Tecnológico

* **Core:** Python 3.10+
* **Framework Web:** FastAPI (con validaciones de Pydantic)
* **Contenedorización:** Docker
* **Especificación:** LaTeX (MikTeX / TeX Live)

---

## ⚙️ Configuración y Ejecución Local

### Opción 1: Ejecución con Python Directo

1. **Crear un entorno virtual:**
   ```bash
   python -m venv .venv
   ```

2. **Activar el entorno virtual:**
   * **En Windows (PowerShell):**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   * **En Linux/macOS:**
     ```bash
     source .venv/bin/activate
     ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Levantar el servidor de desarrollo:**
   ```bash
   uvicorn app.main:app --reload
   ```
   El servidor estará disponible en `http://127.0.0.1:8000`.

### Opción 2: Ejecución con Docker

1. **Construir la imagen:**
   ```bash
   docker build -t despacho-grupo6 .
   ```

2. **Ejecutar el contenedor:**
   ```bash
   docker run -d -p 8000:8000 despacho-grupo6
   ```
   El servidor estará disponible en `http://localhost:8000`.

---

## 📖 Documentación Interactiva (Swagger/OpenAPI)

Una vez levantado el servidor, puedes interactuar directamente con el contrato REST simulado a través de:
* **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📋 Resumen del Contrato de la API

El servicio implementa los estándares definidos en el contrato oficial:

### Cabeceras (Headers) Obligatorias

Todas las solicitudes REST deben incluir:
* `X-Request-Id` (UUIDv4): Identificador único de la petición.
* `X-Correlation-Id` (UUIDv4): Identificador para trazabilidad distribuida.
* `X-Consumer` (String): Identifica el cliente que consume el servicio (ej. `G1-marketplace`).
* `Idempotency-Key` (UUIDv4, opcional en lecturas): Clave para garantizar idempotencia en `POST` y `PATCH`.

### Estructura de Errores Unificada
En caso de fallo, la API responde con un esquema plano de 5 campos:
```json
{
  "timestamp": "2026-06-16T17:00:00Z",
  "status": 400,
  "code": "BAD_REQUEST_SHIPMENT",
  "message": "Mensaje descriptivo del error para el cliente.",
  "correlationId": "uuid-correlation-12345"
}
```

### Endpoints REST Simulado (Fase 2)

| Método | Endpoint | Descripción | Consumidores principales |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/shipments` | Crear una orden de despacho (*Shipment*) | Grupo 8 (Ventas) / Integración |
| `GET` | `/api/v1/shipments/{shipment_id}` | Obtener estado detallado de un despacho | Clientes, Grupo 8 |
| `GET` | `/api/v1/shipments` | Listar despachos con filtros y paginación | Administración / Operaciones |
| `PATCH` | `/api/v1/shipments/{shipment_id}` | Actualizar estado del despacho (ej. transiciones de entrega) | Simulación interna, Grupo 5 (Bodega) |
| `GET` | `/api/v1/health` | Diagnóstico de salud del servicio | Monitoreo del ecosistema |

---

## ⚡ Flujo de Eventos (Asincronía)

El servicio publica actualizaciones en el tópico Kafka `shipment-events`. El sobre (*envelope*) de los eventos utiliza la convención **camelCase** y consta de la siguiente cabecera estándar:

```json
{
  "eventId": "uuid-evento-9999",
  "eventType": "ShipmentCreated",
  "version": "1.0",
  "occurredAt": "2026-06-16T17:05:00Z",
  "producer": "G6-despacho",
  "correlationId": "uuid-correlation-12345",
  "data": { ... }
}
```

### Eventos Publicados
1. **`ShipmentCreated`**: Despacho creado con éxito.
2. **`ShipmentInTransit`**: El despacho ha salido de bodega física.
3. **`ShipmentDelivered`**: El transportista entregó el producto al destinatario final.
4. **`ShipmentCancelled`**: Cancelación de orden de despacho.
5. **`ShipmentFailed`**: Fallo crítico o dirección inaccesible.
6. **`ShipmentReturned`**: El producto regresó al centro logístico.
