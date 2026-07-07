from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from app.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(String, primary_key=True, index=True)
    order_id = Column(String, index=True) # Removed unique=True to allow multiple shipments per order
    customer_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    origin_cd = Column(String, nullable=False)
    volumetric_weight = Column(Float, nullable=False)
    shipping_cost = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    estimated_delivery = Column(DateTime, nullable=True)

class ShipmentStatusHistory(Base):
    __tablename__ = "shipment_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shipment_id = Column(String, ForeignKey("shipments.shipment_id"), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
