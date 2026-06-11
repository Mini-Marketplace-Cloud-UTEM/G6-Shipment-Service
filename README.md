# Servicio de Despacho y Logística (Grupo 6)

Este es el servicio de mock funcional para la Fase 2 del proyecto Marketplace Cloud. Proporciona respuestas simuladas que siguen estrictamente los contratos acordados.

## Requisitos
- Python 3.10 o superior

## Configuración del Entorno Local

1. Crear un entorno virtual:
   ```bash
   python -m venv .venv
   ```
2. Activar el entorno virtual:
   - **En Windows (PowerShell):**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **En Linux/macOS:**
     ```bash
     source .venv/bin/activate
     ```
3. Instalar las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Levantar el Servidor
Ejecuta el servidor de desarrollo:
```bash
uvicorn app.main:app --reload
```

El servidor estará corriendo en `http://127.0.0.1:8000`.

## Documentación Interactiva (Swagger)
Una vez levantado el servidor, puedes interactuar con la API directamente desde tu navegador:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Endpoints Implementados (Fase 2 Mock)
- `POST /api/v1/shipments` --- Crear despacho
- `GET /api/v1/shipments/{shipment_id}` --- Consultar estado por ID
- `GET /api/v1/shipments?order_id={order_id}` --- Buscar por Order ID
- `PATCH /api/v1/shipments/{shipment_id}` --- Actualizar estado (simulación)
- `GET /api/v1/shipments` --- Listar todos los despachos
- `GET /api/v1/health` --- Health check
