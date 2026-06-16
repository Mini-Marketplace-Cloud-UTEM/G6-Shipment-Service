from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator

class ShipmentStatus(str, Enum):
    PENDING = "PENDING"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RETURNED = "RETURNED"

class ShipmentCreate(BaseModel):
    order_id: str = Field(..., description="ID único del pedido de G5")
    customer_name: str = Field(..., max_length=200, description="Nombre del destinatario")
    address: str = Field(..., max_length=500, description="Dirección física de entrega")
    city: str = Field(..., max_length=100, description="Ciudad de destino")
    weight_kg: float = Field(..., gt=0, le=500.0, description="Peso del paquete en kg, debe ser mayor a 0")

    @field_validator('order_id', 'customer_name', 'address', 'city')
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El campo no puede estar vacío o contener solo espacios")
        return v.strip()

class ShipmentResponse(BaseModel):
    shipment_id: str
    order_id: str
    customer_name: str
    address: str
    city: str
    weight_kg: float
    status: ShipmentStatus
    created_at: datetime
    updated_at: datetime
    estimated_delivery: Optional[datetime] = None

class ShipmentUpdate(BaseModel):
    status: ShipmentStatus = Field(..., description="Nuevo estado para la transición")

class ShipmentUpdateResponse(BaseModel):
    shipment_id: str
    order_id: str
    status: ShipmentStatus
    previous_status: ShipmentStatus
    updated_at: datetime

class ShipmentListItem(BaseModel):
    shipment_id: str
    order_id: str
    status: ShipmentStatus
    city: str
    created_at: datetime
    updated_at: datetime

class ShipmentListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    shipments: List[ShipmentListItem]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime

class ErrorResponse(BaseModel):
    timestamp: datetime
    status: int
    code: str
    message: str
    correlationId: str
