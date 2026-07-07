from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class ShipmentStatus(str, Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RETURNED = "RETURNED"

class OriginCD(str, Enum):
    NORTE = "NORTE"
    CENTRO = "CENTRO"
    SUR = "SUR"

class DimensionsCm(CamelModel):
    length: float = Field(..., gt=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)

class PackageInput(CamelModel):
    origin_cd: OriginCD
    weight_kg: float = Field(..., gt=0)
    dimensions_cm: DimensionsCm

class QuoteRequest(CamelModel):
    city: Optional[str] = Field(None, max_length=100, description="Ciudad de destino (Modo Oficial)")
    packages: Optional[List[PackageInput]] = Field(None, description="Lista de paquetes físicos (Modo Oficial)")
    order_total_amount: Optional[int] = Field(None, description="Monto total de la orden. Usado como parche de contingencia (5% de cobro) si no vienen city ni packages.")

class Money(CamelModel):
    amount: int = Field(..., description="Monto en int64")
    currency: str = Field("CLP", description="Moneda (siempre CLP)")

class QuoteResponse(CamelModel):
    total_shipping_cost: Money

class ShipmentCreate(CamelModel):
    order_id: str = Field(..., description="ID único del pedido de G5")
    customer_name: str = Field(..., max_length=200, description="Nombre del destinatario")
    address: str = Field(..., max_length=500, description="Dirección física de entrega")
    city: str = Field(..., max_length=100, description="Ciudad de destino")
    packages: List[PackageInput]

    @field_validator('order_id', 'customer_name', 'address', 'city')
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío o contener solo espacios")
        return v.strip()

class ShipmentCreateResponse(CamelModel):
    shipment_ids: List[str] = Field(..., description="Lista de IDs de despachos creados")

class ShipmentResponse(CamelModel):
    shipment_id: str
    order_id: str
    customer_name: str
    address: str
    city: str
    origin_cd: str
    volumetric_weight: float
    shipping_cost: Money
    weight_kg: float
    status: ShipmentStatus
    created_at: datetime
    updated_at: datetime
    estimated_delivery: Optional[datetime] = None

class ShipmentUpdate(CamelModel):
    status: ShipmentStatus = Field(..., description="Nuevo estado para la transición")

class ShipmentUpdateResponse(CamelModel):
    shipment_id: str
    order_id: str
    status: ShipmentStatus
    previous_status: ShipmentStatus
    updated_at: datetime

class ShipmentListItem(CamelModel):
    shipment_id: str
    order_id: str
    status: ShipmentStatus
    city: str
    created_at: datetime
    updated_at: datetime

class Pagination(CamelModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class ShipmentListResponse(CamelModel):
    data: List[ShipmentListItem]
    pagination: Pagination

class HealthResponse(CamelModel):
    status: str
    service: str
    version: str
    timestamp: datetime

class ErrorDetail(CamelModel):
    field: str
    message: str

class ErrorResponse(CamelModel):
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    correlation_id: Optional[str] = None

class ShipmentHistoryEvent(CamelModel):
    status: ShipmentStatus
    created_at: datetime

class ShipmentHistoryResponse(CamelModel):
    shipment_id: str
    history: List[ShipmentHistoryEvent]
