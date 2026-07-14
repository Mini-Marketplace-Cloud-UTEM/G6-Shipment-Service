from datetime import datetime, timedelta, timezone
import uuid
from typing import Optional, List, Union

from fastapi import FastAPI, Query, status, Depends, Request, Header, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import Shipment, ShipmentStatusHistory, OutboxEvent
from app.schemas import (
    ShipmentCreate,
    ShipmentResponse,
    ShipmentUpdate,
    ShipmentUpdateResponse,
    ShipmentListResponse,
    ShipmentListItem,
    Pagination,
    HealthResponse,
    ErrorResponse,
    ShipmentStatus,
    QuoteRequest,
    QuoteResponse,
    OriginCD,
    ShipmentHistoryResponse,
    ShipmentCreateResponse,
    PackageSize
)

import logging

# Configuración básica de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Inicializar Base de Datos (crea la tabla si no existe)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de Despacho y Logística --- Grupo 6",
    description="Servicio de gestión de despachos v1.3",
    version="1.3.0"
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

# --- Pricing Engine Constants ---
ZONE_MAP = {
    "NORTE": {"NORTE": "MISMA", "CENTRO_NORTE": "ADYACENTE", "CENTRO": "EXTREMA", "CENTRO_SUR": "EXTREMA", "SUR": "EXTREMA"},
    "CENTRO": {"NORTE": "EXTREMA", "CENTRO_NORTE": "ADYACENTE", "CENTRO": "MISMA", "CENTRO_SUR": "ADYACENTE", "SUR": "EXTREMA"},
    "SUR": {"NORTE": "EXTREMA", "CENTRO_NORTE": "EXTREMA", "CENTRO": "EXTREMA", "CENTRO_SUR": "ADYACENTE", "SUR": "MISMA"},
}
CITY_ZONE = {
    "Arica": "NORTE", "Iquique": "NORTE", "Antofagasta": "NORTE",
    "Copiapó": "CENTRO_NORTE", "La Serena": "CENTRO_NORTE", "Coquimbo": "CENTRO_NORTE",
    "Santiago": "CENTRO", "Valparaíso": "CENTRO", "Rancagua": "CENTRO",
    "Talca": "CENTRO_SUR", "Chillán": "CENTRO_SUR", "Concepción": "CENTRO_SUR",
    "Temuco": "SUR", "Valdivia": "SUR", "Puerto Montt": "SUR", "Punta Arenas": "SUR",
}
TARIFF = {
    "MISMA":     {"base": 3000, "per_kg": 500},
    "ADYACENTE": {"base": 5000, "per_kg": 800},
    "EXTREMA":   {"base": 8000, "per_kg": 1200},
}

SIZE_WEIGHT_MAP = {
    PackageSize.XS: 1.0,
    PackageSize.S: 2.0,
    PackageSize.M: 5.0,
    PackageSize.L: 10.0,
    PackageSize.XL: 20.0,
    PackageSize.XXL: 40.0,
}

def calculate_shipping_cost(city: str, origin_cd: str, size: PackageSize) -> tuple[float, int]:
    billable_weight = SIZE_WEIGHT_MAP.get(size, 1.0)
    
    # Resolucion de zona de destino. Si no se encuentra, por defecto se cobra como EXTREMA.
    dest_zone = CITY_ZONE.get(city, "EXTREMA")
    
    # Resolucion de tipo de tarifa (MISMA, ADYACENTE, EXTREMA)
    tariff_type = ZONE_MAP.get(origin_cd, {}).get(dest_zone, "EXTREMA")
    
    tariff = TARIFF[tariff_type]
    cost = tariff["base"] + (tariff["per_kg"] * billable_weight)
    
    return billable_weight, int(cost)


def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-Id", "unknown")

# Manejador personalizado de errores de validación
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for error in exc.errors():
        field = ".".join([str(loc) for loc in error.get("loc", []) if loc != "body"])
        details.append({"field": field, "message": error.get("msg", "Error de validación")})

    error_response = ErrorResponse(
        code="VALIDATION_ERROR",
        message="Error de validación en los campos de entrada.",
        details=details,
        correlation_id=get_correlation_id(request)
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response)
    )

def make_error_response(code: int, err_code: str, message: str, correlation_id: str) -> JSONResponse:
    error_response = ErrorResponse(
        code=err_code,
        message=message,
        correlation_id=correlation_id
    )
    return JSONResponse(status_code=code, content=jsonable_encoder(error_response))

from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = "INTERNAL_ERROR"
    if exc.status_code == 404:
        code = "RESOURCE_NOT_FOUND"
    elif exc.status_code == 400:
        code = "BAD_REQUEST"
    elif exc.status_code == 409:
        code = "CONFLICT"
        
    error_response = ErrorResponse(
        code=code,
        message=exc.detail,
        correlation_id=get_correlation_id(request)
    )
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(error_response))

# Dependencia para validar headers
async def verify_headers(
    x_request_id: str = Header(..., description="Identificador único de la petición"),
    x_correlation_id: str = Header(..., description="Identificador para trazabilidad distribuida"),
    x_consumer: str = Header(..., description="Identifica el cliente que consume el servicio")
):
    pass

error_responses = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
}

@app.post("/api/v1/shipments/quotes", response_model=QuoteResponse, responses=error_responses)
async def quote_shipment(
    request: QuoteRequest = Body(
        ...,
        openapi_examples={
            "Ejemplo Cotización": {
                "summary": "Cotización (Cálculo por Tallas)",
                "description": "Requiere que se envíe la ciudad destino y los paquetes con su talla.",
                "value": {
                    "city": "Santiago",
                    "packages": [
                        {
                            "originCd": "NORTE",
                            "size": "M"
                        }
                    ]
                }
            }
        }
    )
):
    logger.info(f"Cotizando envío para ciudad: {request.city}")
    total_cost = 0
    for pkg in request.packages:
        _, cost = calculate_shipping_cost(request.city, pkg.origin_cd.value, pkg.size)
        total_cost += cost
    logger.info(f"Costo calculado: {total_cost} CLP")
    return QuoteResponse(total_shipping_cost={"amount": total_cost, "currency": "CLP"})


@app.post("/api/v1/shipments", response_model=ShipmentCreateResponse, status_code=status.HTTP_201_CREATED, responses=error_responses, dependencies=[Depends(verify_headers)])
async def create_shipment(request: Request, shipment_data: ShipmentCreate, db: Session = Depends(get_db)):
    correlation_id = get_correlation_id(request)
    logger.info(f"[corr_id: {correlation_id}] POST /api/v1/shipments - Creando nuevo despacho para orden: {shipment_data.order_id}")
            
    now = datetime.now(timezone.utc)
    estimated = now + timedelta(days=3)
    
    shipment_ids = []
    total_packages = len(shipment_data.packages)
    
    today_str = now.strftime("%Y%m%d")
    prefix = f"SHP-{today_str}-"
    count_today = db.query(Shipment).filter(Shipment.shipment_id.like(f"{prefix}%")).count()
    
    for idx, pkg in enumerate(shipment_data.packages, start=1):
        shipment_seq = count_today + idx
        shipment_id = f"{prefix}{shipment_seq:03d}"
        shipment_ids.append(shipment_id)
        
        billable_weight, shipping_cost = calculate_shipping_cost(
            shipment_data.city, pkg.origin_cd.value, pkg.size
        )
        
        # 1. Create Shipment
        new_shipment = Shipment(
            shipment_id=shipment_id,
            order_id=shipment_data.order_id,
            customer_name=shipment_data.customer_name,
            address=shipment_data.address,
            city=shipment_data.city,
            origin_cd=pkg.origin_cd.value,
            volumetric_weight=billable_weight,  # Guardamos el peso equivalente
            shipping_cost=shipping_cost,
            weight_kg=billable_weight,          # Guardamos el peso equivalente
            status=ShipmentStatus.PENDING,
            created_at=now,
            updated_at=now,
            estimated_delivery=estimated
        )
        db.add(new_shipment)
        
        # 2. Create Status History
        history = ShipmentStatusHistory(
            shipment_id=shipment_id,
            status=ShipmentStatus.PENDING,
            created_at=now
        )
        db.add(history)
        
        # 3. Create Outbox Event
        event_payload = {
            "eventId": str(uuid.uuid4()),
            "eventType": "SHIPMENT_CREATED",
            "version": "1.1",
            "occurredAt": now.isoformat(),
            "producer": "g6-despacho",
            "correlationId": correlation_id,
            "payload": {
                "shipmentId": shipment_id,
                "orderId": shipment_data.order_id,
                "customerName": shipment_data.customer_name,
                "address": shipment_data.address,
                "city": shipment_data.city,
                "weightKg": billable_weight,
                "status": ShipmentStatus.PENDING.value,
                "estimatedDelivery": estimated.isoformat() if estimated else None,
                "packageIndex": idx,
                "totalPackages": total_packages
            }
        }
        outbox_event = OutboxEvent(
            event_type="SHIPMENT_CREATED",
            payload=event_payload,
            status="PENDING",
            created_at=now
        )
        db.add(outbox_event)
        
    db.commit()
    return ShipmentCreateResponse(shipment_ids=shipment_ids)

def _format_shipment(s: Shipment) -> dict:
    if s.created_at and not s.created_at.tzinfo:
        s.created_at = s.created_at.replace(tzinfo=timezone.utc)
    if s.updated_at and not s.updated_at.tzinfo:
        s.updated_at = s.updated_at.replace(tzinfo=timezone.utc)
    if s.estimated_delivery and not s.estimated_delivery.tzinfo:
        s.estimated_delivery = s.estimated_delivery.replace(tzinfo=timezone.utc)
        
    return {
        "shipment_id": s.shipment_id,
        "order_id": s.order_id,
        "customer_name": s.customer_name,
        "address": s.address,
        "city": s.city,
        "origin_cd": s.origin_cd,
        "volumetric_weight": s.volumetric_weight,
        "shipping_cost": {"amount": s.shipping_cost, "currency": "CLP"},
        "weight_kg": s.weight_kg,
        "status": s.status,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
        "estimated_delivery": s.estimated_delivery
    }


@app.get("/api/v1/shipments", response_model=Union[ShipmentListResponse, List[ShipmentResponse]], responses=error_responses, dependencies=[Depends(verify_headers)])
async def get_shipments(
    request: Request,
    order_id: Optional[str] = Query(None, alias="orderId"),
    status_filter: Optional[ShipmentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    db: Session = Depends(get_db)
):
    correlation_id = get_correlation_id(request)
    
    # Caso 1: Buscar por Order ID (retorna array de ShipmentResponse)
    if order_id:
        shipments = db.query(Shipment).filter(Shipment.order_id == order_id).all()
        if shipments:
            return [ShipmentResponse(**_format_shipment(s)) for s in shipments]
        
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_code="NOT_FOUND",
            message=f"No se encontró despacho para el pedido {order_id}.",
            correlation_id=correlation_id
        )
        
    # Caso 2: Listar despachos con filtros y paginación
    query = db.query(Shipment)
    if status_filter:
        query = query.filter(Shipment.status == status_filter.value)
        
    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    offset = (page - 1) * page_size
    
    shipments = query.offset(offset).limit(page_size).all()
    
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
    
    pagination = Pagination(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return ShipmentListResponse(
        data=items,
        pagination=pagination
    )


@app.get("/api/v1/shipments/{shipment_id}", response_model=ShipmentResponse, responses=error_responses, dependencies=[Depends(verify_headers)])
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
        
    return _format_shipment(shipment)


@app.patch("/api/v1/shipments/{shipment_id}", response_model=ShipmentUpdateResponse, responses=error_responses, dependencies=[Depends(verify_headers)])
async def update_shipment_status(request: Request, shipment_id: str, update_data: ShipmentUpdate, db: Session = Depends(get_db)):
    correlation_id = get_correlation_id(request)
    logger.info(f"[corr_id: {correlation_id}] PATCH /api/v1/shipments/{shipment_id} - Actualizando estado a {update_data.status.value}")
    
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_code="NOT_FOUND",
            message=f"No se encontró el despacho con ID {shipment_id}.",
            correlation_id=correlation_id
        )
        
    current_status = shipment.status
    new_status = update_data.status.value
    
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
    if new_status not in VALID_TRANSITIONS.get(ShipmentStatus(current_status), set()):
        return make_error_response(
            code=status.HTTP_409_CONFLICT,
            err_code="CONFLICT",
            message=f"Transición de estado no permitida: {current_status} -> {new_status}.",
            correlation_id=correlation_id
        )
        
    now = datetime.now(timezone.utc)
    shipment.status = new_status
    shipment.updated_at = now
    
    # 2. Add history record
    history = ShipmentStatusHistory(
        shipment_id=shipment_id,
        status=new_status,
        created_at=now
    )
    db.add(history)
    
    # 3. Add outbox event
    event_type = f"SHIPMENT_{new_status.upper()}"
    
    # Calcular packageIndex y totalPackages para entregas parciales
    all_shipments = db.query(Shipment).filter(
        Shipment.order_id == shipment.order_id
    ).order_by(Shipment.created_at.asc()).all()
    total_packages = len(all_shipments)
    package_index = next(
        (i for i, s in enumerate(all_shipments, 1) if s.shipment_id == shipment_id), 1
    )
    
    event_payload = {
        "eventId": str(uuid.uuid4()),
        "eventType": event_type,
        "version": "1.1",
        "occurredAt": now.isoformat(),
        "producer": "g6-despacho",
        "correlationId": correlation_id,
        "payload": {
            "shipmentId": shipment_id,
            "orderId": shipment.order_id,
            "customerName": shipment.customer_name,
            "city": shipment.city,
            "newStatus": new_status,
            "previousStatus": current_status,
            "packageIndex": package_index,
            "totalPackages": total_packages
        }
    }
    outbox_event = OutboxEvent(
        event_type=event_type,
        payload=event_payload,
        status="PENDING",
        created_at=now
    )
    db.add(outbox_event)
    
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


@app.get("/api/v1/shipments/{shipment_id}/history", response_model=ShipmentHistoryResponse, responses=error_responses, dependencies=[Depends(verify_headers)])
async def get_shipment_history(request: Request, shipment_id: str, db: Session = Depends(get_db)):
    correlation_id = get_correlation_id(request)
    
    shipment = db.query(Shipment).filter(Shipment.shipment_id == shipment_id).first()
    if not shipment:
        return make_error_response(
            code=status.HTTP_404_NOT_FOUND,
            err_code="NOT_FOUND",
            message=f"No se encontró el despacho con ID {shipment_id}.",
            correlation_id=correlation_id
        )
        
    history = db.query(ShipmentStatusHistory).filter(ShipmentStatusHistory.shipment_id == shipment_id).order_by(ShipmentStatusHistory.created_at.asc()).all()
    
    events = []
    for h in history:
        created_at = h.created_at
        if created_at and not created_at.tzinfo:
            created_at = created_at.replace(tzinfo=timezone.utc)
        events.append({
            "status": h.status,
            "createdAt": created_at.isoformat()
        })
        
    return {
        "shipmentId": shipment_id,
        "history": events
    }


@app.get("/", operation_id="root_endpoint")
async def root():
    return {"message": "API de Despacho y Logística --- Grupo 6 is running. Visit /docs for documentation."}

@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        service="g6-despacho",
        version="1.2.0",
        timestamp=datetime.now(timezone.utc)
    )
