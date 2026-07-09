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
                "size": "S"
            }
        ]
    }
    response = client.post("/api/v1/shipments/quotes", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Size S = 2.0kg. Cost = 3000 (base) + 500 * 2 = 4000
    assert data["totalShippingCost"]["amount"] == 4000
    assert data["totalShippingCost"]["currency"] == "CLP"

def test_quote_shipment_extrema():
    # Temuco is SUR, Origin is NORTE -> EXTREMA zona
    payload = {
        "city": "Temuco",
        "packages": [
            {
                "originCd": "NORTE",
                "size": "XXL"
            }
        ]
    }
    response = client.post("/api/v1/shipments/quotes", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Size XXL = 40.0kg. Cost = 8000 (base) + 1200 * 40 = 56000
    assert data["totalShippingCost"]["amount"] == 56000

def test_quote_validation_error():
    # Missing required field 'city'
    payload = {
        "packages": [
            {
                "originCd": "NORTE",
                "size": "S"
            }
        ]
    }
    response = client.post("/api/v1/shipments/quotes", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "VALIDATION_ERROR"

def test_openapi_is_up_to_date():
    import yaml
    import os
    
    # 1. Obtener OpenAPI directo desde FastAPI en memoria
    openapi_schema = app.openapi()
    
    # 2. Leer el openapi.yaml del disco
    openapi_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'openapi.yaml'))
    
    try:
        with open(openapi_path, "r", encoding="utf-8") as f:
            disk_schema = yaml.safe_load(f)
    except FileNotFoundError:
        assert False, "El archivo openapi.yaml no existe. Corre 'python scripts/dump_openapi.py'"
        
    # 3. Comparar (Normalizando con JSON para evitar diferencias entre tuplas de Python y listas de YAML)
    import json
    schema_normalized = json.loads(json.dumps(openapi_schema))
    disk_normalized = json.loads(json.dumps(disk_schema))
    
    if schema_normalized != disk_normalized:
        assert False, (
            "\n\n=======================================================\n"
            "ERROR DE CALIDAD (QUALITY GATE):\n"
            "El archivo openapi.yaml está DESACTUALIZADO respecto al código.\n"
            "Por favor corre este comando en tu terminal para solucionarlo:\n"
            "    python scripts/dump_openapi.py\n"
            "=======================================================\n"
        )

