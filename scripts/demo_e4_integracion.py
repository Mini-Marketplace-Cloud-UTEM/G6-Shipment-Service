import sys
import os
import uuid
import json
from time import sleep

# Agregar el directorio raíz al path para poder importar la app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import OutboxEvent

client = TestClient(app)

# Colores para la consola
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}={'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {title} {Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}={'='*80}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}[OK] {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}[INFO] {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}[ERROR] {msg}{Colors.ENDC}")

def print_json(data):
    print(f"{Colors.OKBLUE}{json.dumps(data, indent=2, ensure_ascii=False)}{Colors.ENDC}")

def run_demo():
    print_step("INICIANDO DEMOSTRACIÓN TÉCNICA - ENTREGA 4 (GRUPO 6)")
    
    correlation_id = str(uuid.uuid4())
    headers = {
        "X-Request-Id": str(uuid.uuid4()),
        "X-Correlation-Id": correlation_id,
        "X-Consumer": "G4-Checkout",
        "Content-Type": "application/json"
    }
    
    # ---------------------------------------------------------
    # 1. COTIZACIÓN DE ENVÍO (Simulando integración con Checkout)
    # ---------------------------------------------------------
    print_step("1. VALIDACIÓN DE CONTRATO Y PRECIO: Cotización de envío (POST /api/v1/shipments/quotes)")
    print_info(f"Headers enviados (Trazabilidad): X-Correlation-Id={correlation_id}")
    
    quote_payload = {
        "city": "Concepción",
        "packages": [
            {
                "originCd": "CENTRO",
                "weightKg": 5.0,
                "dimensionsCm": {
                    "length": 30,
                    "width": 30,
                    "height": 30
                }
            }
        ]
    }
    
    print_info("Payload enviado:")
    print_json(quote_payload)
    
    response = client.post("/api/v1/shipments/quotes", headers=headers, json=quote_payload)
    
    if response.status_code == 200:
        print_success(f"¡Cotización exitosa! HTTP {response.status_code}")
        print_info("Respuesta de la API:")
        print_json(response.json())
    else:
        print_error(f"Fallo cotización: HTTP {response.status_code}")
        print_json(response.json())
        
    # ---------------------------------------------------------
    # 2. PRUEBA DE CASO FALLIDO (Manejo de Errores)
    # ---------------------------------------------------------
    print_step("2. CASO FALLIDO: Probando validación y manejo de errores estandarizado")
    bad_payload = {
        "packages": [] # Falta la ciudad, fallará validación
    }
    print_info("Enviando payload INVÁLIDO (sin ciudad)...")
    
    response_err = client.post("/api/v1/shipments/quotes", headers=headers, json=bad_payload)
    
    if response_err.status_code == 422:
        print_success(f"¡Manejo de errores correcto! HTTP {response_err.status_code}")
        print_info("Respuesta de Error:")
        print_json(response_err.json())
    else:
        print_error(f"Se esperaba 422, se obtuvo: {response_err.status_code}")
        
    # ---------------------------------------------------------
    # 3. CREACIÓN DE DESPACHO Y GENERACIÓN DE EVENTO (Simulando G5 Pedidos)
    # ---------------------------------------------------------
    print_step("3. INTEGRACIÓN Y PATRÓN TÉCNICO (EVENTOS/OUTBOX): Creación de Despacho")
    
    headers["X-Consumer"] = "G5-Pedidos"
    headers["X-Correlation-Id"] = str(uuid.uuid4())
    order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
    
    create_payload = {
        "orderId": order_id,
        "customerName": "Juan Pérez",
        "address": "Av. Siempreviva 123",
        "city": "Concepción",
        "packages": [
            {
                "originCd": "CENTRO",
                "weightKg": 5.0,
                "dimensionsCm": {
                    "length": 30,
                    "width": 30,
                    "height": 30
                }
            }
        ]
    }
    
    print_info(f"Enviando solicitud de creación de despacho para pedido {order_id}...")
    response_create = client.post("/api/v1/shipments", headers=headers, json=create_payload)
    
    shipment_id = None
    if response_create.status_code == 201:
        print_success(f"¡Despacho creado exitosamente! HTTP {response_create.status_code}")
        data = response_create.json()
        print_json(data)
        shipment_id = data["shipmentIds"][0]
    else:
        print_error(f"Error al crear despacho: HTTP {response_create.status_code}")
        return
        
    # ---------------------------------------------------------
    # 4. ACTUALIZACIÓN DE ESTADO (Para generar un segundo evento)
    # ---------------------------------------------------------
    print_step("4. CAMBIO DE ESTADO (Despacho -> IN_TRANSIT)")
    
    patch_payload = {
        "status": "IN_TRANSIT"
    }
    response_patch = client.patch(f"/api/v1/shipments/{shipment_id}", headers=headers, json=patch_payload)
    
    if response_patch.status_code == 200:
        print_success(f"¡Estado actualizado exitosamente! HTTP {response_patch.status_code}")
        print_json(response_patch.json())
    else:
        print_error(f"Error al actualizar estado: HTTP {response_patch.status_code}")
        
    # ---------------------------------------------------------
    # 5. VERIFICACIÓN DIRECTA DE EVENTOS EN BASE DE DATOS (PATRÓN OUTBOX)
    # ---------------------------------------------------------
    print_step("5. VERIFICACIÓN DE PATRÓN OUTBOX (Eventos listos para Kafka)")
    print_info("Consultando la tabla 'outbox_events' en la base de datos...")
    
    db = SessionLocal()
    try:
        # Obtenemos los eventos más recientes generados
        events = db.query(OutboxEvent).order_by(OutboxEvent.created_at.desc()).limit(2).all()
        
        if events:
            print_success(f"Se encontraron {len(events)} eventos recientes generados correctamente por el servicio:")
            for event in reversed(events): # Mostrar el más viejo primero (creación, luego actualización)
                payload = event.payload if isinstance(event.payload, dict) else json.loads(event.payload)
                print(f"\n{Colors.WARNING}>> Evento: {event.event_type} | Estado BD: {event.status}{Colors.ENDC}")
                print_json(payload)
        else:
            print_error("No se encontraron eventos en el Outbox.")
    except Exception as e:
        print_error(f"Error al conectar a la base de datos: {str(e)}")
    finally:
        db.close()
        
    print_step("FIN DE LA DEMOSTRACIÓN")
    print_info("Estos resultados sirven como evidencia para la Rúbrica de Entrega 4:")
    print(" - Integración y Contratos (Paso 1)")
    print(" - Manejo de errores y Casos fallidos (Paso 2)")
    print(" - Patrón Técnico Eventos/PubSub (Paso 5)")
    print(" - Trazabilidad (Headers enviados en todas las peticiones)\n")


if __name__ == "__main__":
    run_demo()
