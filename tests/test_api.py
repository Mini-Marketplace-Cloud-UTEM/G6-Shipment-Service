from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "g6-despacho"
    assert "version" in data

def test_quote_shipment_misma_zona():
    # Arica is in NORTE, Origin is NORTE -> MISMA zona
    payload = {
        "city": "Arica",
        "packages": [
            {
                "originCd": "NORTE",
                "weightKg": 2.0,
                "dimensionsCm": {
                    "length": 10,
                    "width": 10,
                    "height": 10
                }
            }
        ]
    }
    response = client.post("/api/v1/shipments/quotes", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Volumetric weight = (10*10*10)/4000 = 0.25. Real weight = 2.0. Billable = 2.0.
    # Cost = 3000 (base) + 500 * 2 = 4000
    assert data["totalShippingCost"] == 4000
    assert data["currency"] == "CLP"

def test_quote_shipment_extrema():
    # Temuco is SUR, Origin is NORTE -> EXTREMA zona
    payload = {
        "city": "Temuco",
        "packages": [
            {
                "originCd": "NORTE",
                "weightKg": 10.0,
                "dimensionsCm": {
                    "length": 50,
                    "width": 50,
                    "height": 50
                }
            }
        ]
    }
    response = client.post("/api/v1/shipments/quotes", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Volumetric weight = (50*50*50)/4000 = 125000/4000 = 31.25. Real weight = 10.0. Billable = 31.25.
    # Cost = 8000 (base) + 1200 * 31.25 = 8000 + 37500 = 45500
    assert data["totalShippingCost"] == 45500

def test_quote_validation_error():
    # Missing required field 'city'
    payload = {
        "packages": [
            {
                "originCd": "NORTE",
                "weightKg": 2.0,
                "dimensionsCm": {
                    "length": 10,
                    "width": 10,
                    "height": 10
                }
            }
        ]
    }
    response = client.post("/api/v1/shipments/quotes", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert "details" in data
