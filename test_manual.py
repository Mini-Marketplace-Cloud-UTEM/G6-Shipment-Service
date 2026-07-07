import sys
import json
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)
client = TestClient(app)

payload = {
    'orderId': 'TEST-001',
    'customerName': 'Test User',
    'address': 'Test Address 123',
    'city': 'Santiago',
    'packages': [
        {'originCd': 'NORTE', 'weightKg': 2.5, 'dimensionsCm': {'length': 10, 'width': 10, 'height': 10}},
        {'originCd': 'SUR', 'weightKg': 1.0, 'dimensionsCm': {'length': 5, 'width': 5, 'height': 5}}
    ]
}

headers = {
    'X-Request-Id': 'req-1',
    'X-Correlation-Id': 'corr-1',
    'X-Consumer': 'tester',
    'Idempotency-Key': 'idemp-1'
}

print('=== 1. Creando Despacho ===')
response = client.post('/api/v1/shipments', json=payload, headers=headers)
print('Response POST:', response.status_code, response.json())
shipment_ids = response.json()['shipmentIds']

db = next(get_db())
from app.models import OutboxEvent
events = db.query(OutboxEvent).all()
for e in events:
    print(f'Outbox (POST): {e.event_type} | payload_keys: {list(e.payload.keys())} | packageIndex: {e.payload["payload"].get("packageIndex")} | totalPackages: {e.payload["payload"].get("totalPackages")} | orderId: {e.payload["payload"].get("orderId")}')

print('\n=== 2. Actualizando Estado ===')
patch_payload = {'status': 'IN_TRANSIT'}
response = client.patch(f'/api/v1/shipments/{shipment_ids[0]}', json=patch_payload, headers=headers)
print('Response PATCH:', response.status_code, response.json())

events = db.query(OutboxEvent).order_by(OutboxEvent.id.desc()).limit(1).all()
e = events[0]
print(f'Outbox (PATCH): {e.event_type} | payload_keys: {list(e.payload.keys())} | packageIndex: {e.payload["payload"].get("packageIndex")} | totalPackages: {e.payload["payload"].get("totalPackages")} | orderId: {e.payload["payload"].get("orderId")}')

