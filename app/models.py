from sqlalchemy import Column, String, Float, DateTime
from datetime import datetime, timezone
from app.database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id = Column(String, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    customer_name = Column(String)
    address = Column(String)
    city = Column(String)
    weight_kg = Column(Float)
    status = Column(String)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    estimated_delivery = Column(DateTime, nullable=True)
