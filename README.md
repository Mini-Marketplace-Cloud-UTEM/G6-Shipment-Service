# Servicio de Despacho y Logística — Grupo 6 (Marketplace Cloud)

[![Deploy Status](https://img.shields.io/badge/Render-Mock_E2-blue)](https://g6-despacho.onrender.com/docs)
[![Deploy Status](https://img.shields.io/badge/Render-App_Oficial_E3-brightgreen)](https://g6-despacho-oficial.onrender.com/docs)
**🔗 Link Mock (E2):** [https://g6-despacho.onrender.com/docs](https://g6-despacho.onrender.com/docs)
**🔗 Link API Oficial (E3):** [https://g6-despacho-oficial.onrender.com/docs](https://g6-despacho-oficial.onrender.com/docs)

Este repositorio contiene la especificación, documentación técnica y el prototipo funcional (mock) del **Servicio de Despacho y Logística** (Grupo 6) diseñado para el ecosistema del Marketplace Cloud.

El microservicio se encarga de la gestión del ciclo de vida de los envíos (*Shipments*), desde la recepción de la orden de despacho hasta la entrega final al cliente o su devolución, integrando flujos síncronos (REST) y asíncronos (Eventos/Kafka).

## Calidad y Contratos (Quality Gate)
Para asegurar que el contrato oficial siempre coincida con el código (esquemas Pydantic), se implementó una prueba automatizada (`test_openapi_is_up_to_date`) que fallará si realizas cambios y olvidas actualizar el archivo `openapi.yaml`.

Si esto ocurre, simplemente debes ejecutar el script automático desde la raíz del proyecto para actualizar el Swagger:
```bash
python scripts/dump_openapi.py
```
Esto sobrescribirá el archivo `openapi.yaml` garantizando que todo el equipo (y otros grupos mediante Prism) usen siempre el contrato más reciente y sin errores humanos.

---

## 📂 Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

* **[`app/`](app/)**: Código fuente en Python del mock funcional (FastAPI).
  * [`main.py`](app/main.py): Endpoints, pricing engine y lógica de negocio.
  * [`schemas.py`](app/schemas.py): Modelos Pydantic v1.2 (camelCase).
  * [`models.py`](app/models.py): Modelos SQLAlchemy (PostgreSQL).
  * [`database.py`](app/database.py): Conexión a Supabase.
* **[`docs/`](docs/)**: Documentación técnica oficial.
  * [`contratos/`](docs/contratos/): Contratos de la API REST y eventos.
    * 📑 **[G6_Contrato_API_Despacho.pdf](docs/contratos/G6_Contrato_API_Despacho.pdf)**: Documento compilado final (Consolidado v1.4).
    * 📄 [G6_Contrato_API_Despacho.tex](docs/contratos/G6_Contrato_API_Despacho.tex): Código fuente en LaTeX.
    * Archivos Markdown individuales para la integración de cada grupo (`G1_Frontend.md`, `G4_Inventario_Checkout.md`, etc.).
  * [`briefing/`](docs/briefing/): Briefing técnico del servicio.
    * 📑 **[G6_Logistica_Briefing.pdf](docs/briefing/G6_Logistica_Briefing.pdf)**: Documento compilado final.
    * 📄 [G6_Logistica_Briefing.tex](docs/briefing/G6_Logistica_Briefing.tex): Código fuente en LaTeX.
* **[`openapi.yaml`](openapi.yaml)**: Especificación OpenAPI 3.0.3 v1.4 formal.
* **[`Dockerfile`](Dockerfile)**: Archivo de configuración para la contenedorización del servicio.

---

## 🛠️ Stack Tecnológico

* **Core:** Python 3.10+
* **Framework Web:** FastAPI (con validaciones de Pydantic)
* **Contenedorización:** Docker
* **Especificación:** LaTeX (MikTeX / TeX Live)

---

## ⚙️ Configuración y Ejecución Local

Este servicio ahora utiliza **Supabase (PostgreSQL)** como base de datos. Para ejecutarlo localmente, requieres configurar la variable de entorno `DATABASE_URL`.

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

4. **Configurar Variable de Entorno:**
   Crea un archivo `.env` en la raíz (o configura en tu entorno):
   ```bash
   DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[ref].supabase.co:5432/postgres"
   ```

5. **Levantar el servidor de desarrollo:**
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

### Opción 3: Pruebas Automatizadas y CI/CD (GitHub Actions)

El repositorio cuenta con una suite de pruebas para verificar el motor de precios y la salud de la API. Estas pruebas evalúan los escenarios principales y validación de errores.

**Ejecución Local:**
1. Instalar dependencias de pruebas:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecutar pytest:
   ```bash
   pytest tests/
   ```

**Integración Continua (CI):**
El proyecto implementa un pipeline automatizado mediante **GitHub Actions** (`.github/workflows/ci.yml`). 
Cada vez que se realiza un *push* a las ramas `main` o `E3-dev`, GitHub levanta un servidor temporal, instala las dependencias y ejecuta la suite de `pytest`. Si las pruebas fallan, alerta al equipo para evitar que errores lleguen a producción.

---

## 📖 Documentación Interactiva (Swagger/OpenAPI)

Una vez levantado el servidor, puedes interactuar directamente con el contrato REST simulado a través de:
* **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📋 Modelo de Datos (v1.4)

El mock ahora utiliza PostgreSQL (vía Supabase) con 3 tablas clave para soportar el contrato v1.4:

1. **`shipments`**: Registra individualmente cada caja/paquete (eliminando la restricción UNIQUE en `order_id` para permitir envíos multi-origen). Almacena campos volumétricos, costos (`shipping_cost`), zona de origen (`origin_cd`) y estado actual.
2. **`shipment_status_history`**: Mantiene un historial inmutable de todas las transiciones de estado por cada `shipment_id`.
3. **`outbox_events`**: Implementación del patrón transaccional Outbox. Almacena en la misma transacción de BD los eventos generados (en formato JSON Envelope) listos para ser despachados a Google Cloud Pub/Sub por un worker asíncrono.

---

## 📋 Resumen del Contrato de la API

El servicio implementa los estándares definidos en el contrato oficial v1.4:

### Cabeceras (Headers) Obligatorias

Todas las solicitudes REST deben incluir:
* `X-Request-Id` (UUIDv4): Identificador único de la petición.
* `X-Correlation-Id` (UUIDv4): Identificador para trazabilidad distribuida.
* `X-Consumer` (String): Identifica el cliente que consume el servicio (ej. `G1-marketplace`).
* `Idempotency-Key` (UUIDv4, opcional en lecturas): Clave para garantizar idempotencia en `POST` y `PATCH`.

### Estructura de Errores Unificada
En caso de fallo, la API responde con un esquema alineado al estándar de la organización, que consta de los siguientes campos:
```json
{
  "code": "BAD_REQUEST_SHIPMENT",
  "message": "Mensaje descriptivo del error para el cliente.",
  "details": [
    {
      "field": "nombre_campo",
      "message": "Descripción del error de validación"
    }
  ],
  "correlationId": "uuid-correlation-12345"
}
```

### Endpoints REST Simulado (Fase 2)

| Método | Endpoint | Descripción | Consumidores principales |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/shipments/quotes` | Cotizar envío (Tarifa Consolidada) | Grupo 4 (Checkout) |
| `POST` | `/api/v1/shipments` | Crear despachos multi-origen | Grupo 5 (Pedidos) |
| `GET` | `/api/v1/shipments/{shipment_id}` | Obtener estado detallado de un despacho | Clientes, Grupo 5 |
| `GET` | `/api/v1/shipments` | Listar despachos con filtros y paginación | Grupo 7 (Reportería) |
| `PATCH` | `/api/v1/shipments/{shipment_id}` | Actualizar estado del despacho | Simulación interna |
| `GET` | `/api/v1/health` | Diagnóstico de salud del servicio | Monitoreo del ecosistema |

---

## ⚡ Flujo de Eventos (Asincronía)

El servicio publica actualizaciones en un tópico de **Google Cloud Pub/Sub** mediante un worker del patrón Outbox. El sobre (*envelope*) de los eventos utiliza la convención **camelCase** y consta de la siguiente cabecera estándar:

```json
{
  "eventId": "uuid-evento-9999",
  "eventType": "SHIPMENT_CREATED",
  "version": "1.2",
  "occurredAt": "2026-06-16T17:05:00Z",
  "producer": "g6-despacho",
  "correlationId": "uuid-correlation-12345",
  "payload": { ... }
}
```

### Eventos Publicados
1. **`SHIPMENT_CREATED`**: Despacho creado con éxito.
2. **`SHIPMENT_IN_TRANSIT`**: El despacho ha salido de bodega física.
3. **`SHIPMENT_DELIVERED`**: El transportista entregó el producto al destinatario final.
4. **`SHIPMENT_CANCELLED`**: Cancelación de orden de despacho.
5. **`SHIPMENT_FAILED`**: Fallo crítico o dirección inaccesible.
6. **`SHIPMENT_RETURNED`**: El producto regresó al centro logístico.
