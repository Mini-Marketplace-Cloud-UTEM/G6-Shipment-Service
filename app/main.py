from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional

from fastapi import FastAPI, Query, status, Depends, Request, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import Shipment
from app.schemas import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentUpdate,
    ShipmentUpdateResponse,
    ShipmentListResponse,
    ShipmentListItem,
    HealthResponse,
    ErrorResponse,
    ShipmentStatus
)

# Inicializar Base de Datos (crea la tabla si no existe)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Despacho y Logística --- Grupo 6",
    description="Servicio de gestión de despachos",
    version="1.0.0"
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

def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-Id", "unknown")

# Manejador personalizado de errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        err = errors[0]
        field = ".".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        err_type = err.get('type')
        
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
    else:
        message = "Error de validación de datos."

    error_response = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message=message,
        correlationId=get_correlation_id(request)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response)
    )

def make_error_response(code: int, err_code: str, message: str, correlation_id: str) -> JSONResponse:
    error_response = ErrorResponse(
        timestamp=datetime.now(timezone.utc),
        status=code,
        code=err_code,
        message=message,
        correlationId=correlation_id
    )
    return JSONResponse(status_code=code, content=jsonable_encoder(error_response))

# Dependencia para validar headers
async def verify_headers(
    x_request_id: str = Header(..., description="Identificador único de la petición"),
    x_correlation_id: str = Header(..., description="Identificador para trazabilidad distribuida"),
    x_consumer: str = Header(..., description="Identifica el cliente que consume el servicio")
):
    pass

@app.post("/api/v1/shipments", response_model=ShipmentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_headers)])
async def create_shipment(request: Request, shipment_data: ShipmentCreate, db: Session = Depends(get_db)):
    correlation_id = get_correlation_id(request)
    
    # Validar duplicados de order_id
    existing_shipment = db.query(Shipment).filter(Shipment.order_id == shipment_data.order_id).first()
    if existing_shipment:
        return make_error_response(
            code=status.HTTP_409_CONFLICT,
            err_code="CONFLICT",
            message=f"Ya existe un despacho asociado al pedido {shipment_data.order_id}.",
            correlation_id=correlation_id
        )
            
    shipment_id = f"SHP-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    estimated = now + timedelta(days=3)
    
    new_shipment = Shipment(
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
    
    db.add(new_shipment)
    db.commit()
    db.refresh(new_shipment)
    
    # ensure tzinfo is there for pydantic
    if new_shipment.created_at and not new_shipment.created_at.tzinfo:
        new_shipment.created_at = new_shipment.created_at.replace(tzinfo=timezone.utc)
    if new_shipment.updated_at and not new_shipment.updated_at.tzinfo:
        new_shipment.updated_at = new_shipment.updated_at.replace(tzinfo=timezone.utc)
    if new_shipment.estimated_delivery and not new_shipment.estimated_delivery.tzinfo:
        new_shipment.estimated_delivery = new_shipment.estimated_delivery.replace(tzinfo=timezone.utc)

    return new_shipment

@app.get("/api/v1/shipments/{shipment_id}", response_model=ShipmentResponse, dependencies=[Depends(verify_headers)])
async def get_shipment_by_id(request: Request, shipment_id: str, db: Session = Depends(get_db)):
    correlation_id = get_correlation_id(request)
    
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_code="NOT_FOUND",
            message=f"No se encontró el despacho con ID {shipment_id}.",
            correlation_id=correlation_id
        )
    
    # ensure tzinfo is there for pydantic
    if shipment.created_at and not shipment.created_at.tzinfo:
        shipment.created_at = shipment.created_at.replace(tzinfo=timezone.utc)
    if shipment.updated_at and not shipment.updated_at.tzinfo:
        shipment.updated_at = shipment.updated_at.replace(tzinfo=timezone.utc)
    if shipment.estimated_delivery and not shipment.estimated_delivery.tzinfo:
        shipment.estimated_delivery = shipment.estimated_delivery.replace(tzinfo=timezone.utc)
        
    return shipment

@app.get("/api/v1/shipments", dependencies=[Depends(verify_headers)])
async def get_shipments(
    request: Request,
    order_id: Optional[str] = None,
    status_filter: Optional[ShipmentStatus] = Query(None, alias="status"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    correlation_id = get_correlation_id(request)
    
    # Caso 1: Buscar por Order ID (retorna objeto único o 404)
    if order_id:
        s = db.query(Shipment).filter(Shipment.order_id == order_id).first()
        if s:
            if s.created_at and not s.created_at.tzinfo:
                s.created_at = s.created_at.replace(tzinfo=timezone.utc)
            if s.estimated_delivery and not s.estimated_delivery.tzinfo:
                s.estimated_delivery = s.estimated_delivery.replace(tzinfo=timezone.utc)
                
            return {
                "shipment_id": s.shipment_id,
                "order_id": s.order_id,
                "status": s.status,
                "created_at": s.created_at,
                "estimated_delivery": s.estimated_delivery
            }
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_code="NOT_FOUND",
            message=f"No se encontró despacho para el pedido {order_id}.",
            correlation_id=correlation_id
        )
        
    # Caso 2: Listar despachos con filtros y paginación
    query = db.query(Shipment)
    if status_filter:
        query = query.filter(Shipment.status == status_filter)
        
    total = query.count()
    shipments = query.offset(offset).limit(limit).all()
    
    items = []
    for s in shipments:
        if s.created_at and not s.created_at.tzinfo:
            s.created_at = s.created_at.replace(tzinfo=timezone.utc)
        if s.updated_at and not s.updated_at.tzinfo:
            s.updated_at = s.updated_at.replace(tzinfo=timezone.utc)
            
        items.append(ShipmentListItem(
            shipment_id=s.shipment_id,
            order_id=s.order_id,
            status=s.status,
            city=s.city,
            created_at=s.created_at,
            updated_at=s.updated_at
        ))
    
    return ShipmentListResponse(
        total=total,
        limit=limit,
        offset=offset,
        shipments=items
    )

@app.patch("/api/v1/shipments/{shipment_id}", response_model=ShipmentUpdateResponse, dependencies=[Depends(verify_headers)])
async def update_shipment_status(request: Request, shipment_id: str, update_data: ShipmentUpdate, db: Session = Depends(get_db)):
    correlation_id = get_correlation_id(request)
    
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_code="NOT_FOUND",
            message=f"No se encontró el despacho con ID {shipment_id}.",
            correlation_id=correlation_id
        )
        
    current_status = shipment.status
    new_status = update_data.status
    
    # Si es el mismo estado, no hay cambios pero se actualiza la fecha
    if current_status == new_status:
        now = datetime.now(timezone.utc)
        shipment.updated_at = now
        db.commit()
        db.refresh(shipment)
        
        if shipment.updated_at and not shipment.updated_at.tzinfo:
            shipment.updated_at = shipment.updated_at.replace(tzinfo=timezone.utc)
            
        return ShipmentUpdateResponse(
            shipment_id=shipment.shipment_id,
            order_id=shipment.order_id,
            status=shipment.status,
            previous_status=current_status,
            updated_at=shipment.updated_at
        )
        
    # Validar transición de estado
    if new_status not in VALID_TRANSITIONS.get(current_status, set()):
        return make_error_response(
            code=status.HTTP_409_CONFLICT,
            err_code="CONFLICT",
            message=f"Transición de estado no permitida: {current_status} -> {new_status}.",
            correlation_id=correlation_id
        )
        
    now = datetime.now(timezone.utc)
    shipment.status = new_status
    shipment.updated_at = now
    db.commit()
    db.refresh(shipment)
    
    if shipment.updated_at and not shipment.updated_at.tzinfo:
        shipment.updated_at = shipment.updated_at.replace(tzinfo=timezone.utc)
    
    return ShipmentUpdateResponse(
        shipment_id=shipment.shipment_id,
        order_id=shipment.order_id,
        status=shipment.status,
        previous_status=current_status,
        updated_at=shipment.updated_at
    )

@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        service="g6-despacho",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc)
    )
