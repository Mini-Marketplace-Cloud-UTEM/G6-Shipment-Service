from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional
from fastapi import FastAPI, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from app.schemas import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentUpdate,
    ShipmentUpdateResponse,
    ShipmentListResponse,
    ShipmentListItem,
    HealthResponse,
    ErrorResponse,
    ErrorDetail,
    ValidationErrorDetail,
    ShipmentStatus
)

app = FastAPI(
    title="API de Despacho y Logística --- Grupo 6",
    description="Servicio de mock funcional para simulación de despachos",
    version="1.0.0"
)

# Base de datos en memoria
db_shipments = {}

# Seeding inicial para pruebas rápidas
initial_shipment_id = "SHP-a1b2c3d4"
db_shipments[initial_shipment_id] = ShipmentResponse(
    shipment_id=initial_shipment_id,
    order_id="ORD-20260611-001",
    customer_name="María González",
    address="Av. Providencia 1234, Depto 56",
    city="Santiago",
    weight_kg=3.2,
    status=ShipmentStatus.PENDING,
    created_at=datetime.fromisoformat("2026-06-11T14:00:00+00:00"),
    updated_at=datetime.fromisoformat("2026-06-11T14:00:00+00:00"),
    estimated_delivery=datetime.fromisoformat("2026-06-14T18:00:00+00:00")
)

# Transiciones de estado permitidas
VALID_TRANSITIONS = {
    ShipmentStatus.PENDING: {ShipmentStatus.IN_TRANSIT, ShipmentStatus.CANCELLED},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.DELIVERED, ShipmentStatus.FAILED},
    ShipmentStatus.DELIVERED: {ShipmentStatus.RETURNED},
    ShipmentStatus.CANCELLED: set(),
    ShipmentStatus.FAILED: set(),
    ShipmentStatus.RETURNED: set()
}

# Manejador personalizado de errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    if errors:
        err = errors[0]
        # Limpiar ruta de campo para mejor legibilidad
        field = ".".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        input_value = err.get('input')
        err_type = err.get('type')
        
        # Personalizar mensajes
        if err_type == 'missing':
            message = f"El campo {field} es obligatorio."
        elif err_type == 'greater_than':
            limit = err.get('ctx', {}).get('gt')
            message = f"El campo {field} debe ser mayor a {limit}."
        elif err_type == 'less_than_equal':
            limit = err.get('ctx', {}).get('le')
            message = f"El campo {field} debe ser menor o igual a {limit}."
        else:
            message = f"El campo {field} no es válido: {err.get('msg')}."
        
        detail = ValidationErrorDetail(
            field=field,
            value=input_value,
            constraint=err_type
        )
    else:
        message = "Error de validación de datos."
        detail = None

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=422,
            type="VALIDATION_ERROR",
            message=message,
            details=detail
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response)
    )

def make_error_response(code: int, err_type: str, message: str) -> JSONResponse:
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            type=err_type,
            message=message
        )
    )
    return JSONResponse(status_code=code, content=jsonable_encoder(error_response))

@app.post("/api/v1/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(shipment_data: ShipmentCreate):
    # Validar duplicados de order_id
    for s in db_shipments.values():
        if s.order_id == shipment_data.order_id:
            return make_error_response(
                code=status.HTTP_409_CONFLICT,
                err_type="CONFLICT",
                message=f"Ya existe un despacho asociado al pedido {shipment_data.order_id}."
            )
            
    shipment_id = f"SHP-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    estimated = now + timedelta(days=3)
    
    shipment = ShipmentResponse(
        shipment_id=shipment_id,
        order_id=shipment_data.order_id,
        customer_name=shipment_data.customer_name,
        address=shipment_data.address,
        city=shipment_data.city,
        weight_kg=shipment_data.weight_kg,
        status=ShipmentStatus.PENDING,
        created_at=now,
        updated_at=now,
        estimated_delivery=estimated
    )
    
    db_shipments[shipment_id] = shipment
    return shipment

@app.get("/api/v1/shipments/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment_by_id(shipment_id: str):
    if shipment_id not in db_shipments:
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_type="NOT_FOUND",
            message=f"No se encontró el despacho con ID {shipment_id}."
        )
    return db_shipments[shipment_id]

@app.get("/api/v1/shipments")
async def get_shipments(
    order_id: Optional[str] = None,
    status_filter: Optional[ShipmentStatus] = Query(None, alias="status"),
    limit: int = 50,
    offset: int = 0
):
    # Caso 1: Buscar por Order ID (retorna objeto único o 404)
    if order_id:
        for s in db_shipments.values():
            if s.order_id == order_id:
                return {
                    "shipment_id": s.shipment_id,
                    "order_id": s.order_id,
                    "status": s.status,
                    "created_at": s.created_at,
                    "estimated_delivery": s.estimated_delivery
                }
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_type="NOT_FOUND",
            message=f"No se encontró despacho para el pedido {order_id}."
        )
        
    # Caso 2: Listar despachos con filtros y paginación
    shipments_list = list(db_shipments.values())
    if status_filter:
        shipments_list = [s for s in shipments_list if s.status == status_filter]
        
    total = len(shipments_list)
    paginated = shipments_list[offset:offset+limit]
    
    items = [
        ShipmentListItem(
            shipment_id=s.shipment_id,
            order_id=s.order_id,
            status=s.status,
            city=s.city,
            created_at=s.created_at,
            updated_at=s.updated_at
        ) for s in paginated
    ]
    
    return ShipmentListResponse(
        total=total,
        limit=limit,
        offset=offset,
        shipments=items
    )

@app.patch("/api/v1/shipments/{shipment_id}", response_model=ShipmentUpdateResponse)
async def update_shipment_status(shipment_id: str, update_data: ShipmentUpdate):
    if shipment_id not in db_shipments:
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_type="NOT_FOUND",
            message=f"No se encontró el despacho con ID {shipment_id}."
        )
        
    shipment = db_shipments[shipment_id]
    current_status = shipment.status
    new_status = update_data.status
    
    # Si es el mismo estado, no hay cambios pero se actualiza la fecha
    if current_status == new_status:
        now = datetime.now(timezone.utc)
        shipment.updated_at = now
        return ShipmentUpdateResponse(
            shipment_id=shipment.shipment_id,
            order_id=shipment.order_id,
            status=shipment.status,
            previous_status=current_status,
            updated_at=now
        )
        
    # Validar transición de estado
    if new_status not in VALID_TRANSITIONS[current_status]:
        return make_error_response(
            code=status.HTTP_409_CONFLICT,
            err_type="CONFLICT",
            message=f"Transición de estado no permitida: {current_status} -> {new_status}."
        )
        
    now = datetime.now(timezone.utc)
    shipment.status = new_status
    shipment.updated_at = now
    
    return ShipmentUpdateResponse(
        shipment_id=shipment.shipment_id,
        order_id=shipment.order_id,
        status=shipment.status,
        previous_status=current_status,
        updated_at=now
    )

@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        service="g6-despacho",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )
