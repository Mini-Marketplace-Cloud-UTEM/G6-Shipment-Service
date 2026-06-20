# Entregables - Fase 2: Mock y Contratos (Grupo 6 - Despachos)

Este documento centraliza los entregables requeridos para la evaluación **E2 Mock**, alineados con la rúbrica oficial.

## 1. Repositorio GitHub
**URL:** [https://github.com/Mini-Marketplace-Cloud-UTEM/G6-Shipment-Service](https://github.com/Mini-Marketplace-Cloud-UTEM/G6-Shipment-Service)
**Estado:** ¡Excelente! Repositorio configurado, versionado, con historial limpio y ramas protegidas (main).

## 2. Mock público o servicio inicial
**URL:** [https://g6-despacho.onrender.com/docs](https://g6-despacho.onrender.com/docs)
**Estado:** El servicio mock en FastAPI está implementado. *(Nota: La URL definitiva puede estar en proceso de reconexión tras la transferencia de repositorio a la organización).*

## 3. README inicial
**Evidencia:** El archivo README.md se encuentra en la raíz del repositorio, detallando la arquitectura, la configuración local (Docker y Python) y la documentación de la API.
**URL Directa:** [https://github.com/Mini-Marketplace-Cloud-UTEM/G6-Shipment-Service/blob/main/README.md](https://github.com/Mini-Marketplace-Cloud-UTEM/G6-Shipment-Service/blob/main/README.md)

## 4. Modelo de Datos Actualizado
El modelo se refinó en la **versión 1.2** para soportar logística multi-origen, cobro por volumetría y un entorno asíncrono robusto utilizando el patrón *Transactional Outbox*.

### Diagrama Entidad-Relación (Mermaid)
`mermaid
erDiagram
    shipments ||--o{ shipment_status_history : "tiene historial"
    shipments {
        string shipment_id PK "ej: SHP-uuid"
        string order_id "Permite múltiples despachos por orden"
        string origin_cd "ej: CD_SANTIAGO"
        string customer_name
        string address
        string city
        float weight_kg "Debe ser > 0"
        float shipping_cost
        string status "DEFAULT 'PENDING'"
        timestamp created_at
        timestamp updated_at
        timestamp estimated_delivery
    }
    shipment_status_history {
        int id PK
        string shipment_id FK
        string previous_status
        string new_status
        timestamp changed_at "Inmutable"
    }
    outbox_events {
        string eventId PK "UUID autogenerado"
        string eventType "ej: ShipmentCreated"
        jsonb payload "Datos del evento en formato camelCase"
        string status "PENDING, PROCESSED"
        timestamp createdAt
    }
`

## 5. Colección de pruebas de Contrato
Se ha diseñado una colección que prueba los endpoints POST, GET y PATCH validando el contrato, los headers obligatorios (X-Request-Id, X-Correlation-Id, X-Consumer) y los parámetros.

Puedes importar el siguiente bloque JSON directamente en Postman/Insomnia o usar el archivo adjunto postman_collection.json.

`json
{
  "info": {
    "name": "G6 Despacho v1.2",
    "description": "Pruebas de contrato para la API de Despacho v1.2 (Marketplace Cloud)",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "{{base_url}}/api/v1/health",
          "host": [
            "{{base_url}}"
          ],
          "path": [
            "api",
            "v1",
            "health"
          ]
        }
      },
      "response": []
    },
    {
      "name": "Cotizar Envío (Multi-Paquete)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"city\": \"Temuco\",\n  \"packages\": [\n    {\n      \"originCd\": \"CENTRO\",\n      \"weightKg\": 2.5,\n      \"dimensionsCm\": {\n        \"length\": 10,\n        \"width\": 10,\n        \"height\": 10\n      }\n    },\n    {\n      \"originCd\": \"NORTE\",\n      \"weightKg\": 5.0,\n      \"dimensionsCm\": {\n        \"length\": 50,\n        \"width\": 50,\n        \"height\": 50\n      }\n    }\n  ]\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/shipments/quotes",
          "host": [
            "{{base_url}}"
          ],
          "path": [
            "api",
            "v1",
            "shipments",
            "quotes"
          ]
        }
      },
      "response": []
    },
    {
      "name": "Crear Despacho",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "X-Request-Id",
            "value": "req-123"
          },
          {
            "key": "X-Correlation-Id",
            "value": "corr-456"
          },
          {
            "key": "X-Consumer",
            "value": "postman"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"orderId\": \"ORD-TEST-001\",\n  \"customerName\": \"Juan Perez\",\n  \"address\": \"Avenida Siempre Viva 123\",\n  \"city\": \"Santiago\",\n  \"packages\": [\n    {\n      \"originCd\": \"CENTRO\",\n      \"weightKg\": 2.5,\n      \"dimensionsCm\": {\n        \"length\": 10,\n        \"width\": 10,\n        \"height\": 10\n      }\n    }\n  ]\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/shipments",
          "host": [
            "{{base_url}}"
          ],
          "path": [
            "api",
            "v1",
            "shipments"
          ]
        }
      },
      "response": []
    },
    {
      "name": "Buscar Despachos por Order ID",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "X-Request-Id",
            "value": "req-123"
          },
          {
            "key": "X-Correlation-Id",
            "value": "corr-456"
          },
          {
            "key": "X-Consumer",
            "value": "postman"
          }
        ],
        "url": {
          "raw": "{{base_url}}/api/v1/shipments?orderId=ORD-TEST-001",
          "host": [
            "{{base_url}}"
          ],
          "path": [
            "api",
            "v1",
            "shipments"
          ],
          "query": [
            {
              "key": "orderId",
              "value": "ORD-TEST-001"
            }
          ]
        }
      },
      "response": []
    },
    {
      "name": "Obtener Despacho por ID",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "X-Request-Id",
            "value": "req-123"
          },
          {
            "key": "X-Correlation-Id",
            "value": "corr-456"
          },
          {
            "key": "X-Consumer",
            "value": "postman"
          }
        ],
        "url": {
          "raw": "{{base_url}}/api/v1/shipments/SHP-REPLACE-ME",
          "host": [
            "{{base_url}}"
          ],
          "path": [
            "api",
            "v1",
            "shipments",
            "SHP-REPLACE-ME"
          ]
        }
      },
      "response": []
    },
    {
      "name": "Actualizar Estado",
      "request": {
        "method": "PATCH",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "X-Request-Id",
            "value": "req-123"
          },
          {
            "key": "X-Correlation-Id",
            "value": "corr-456"
          },
          {
            "key": "X-Consumer",
            "value": "postman"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"status\": \"IN_TRANSIT\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/v1/shipments/SHP-REPLACE-ME",
          "host": [
            "{{base_url}}"
          ],
          "path": [
            "api",
            "v1",
            "shipments",
            "SHP-REPLACE-ME"
          ]
        }
      },
      "response": []
    },
    {
      "name": "Historial de Estados",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "X-Request-Id",
            "value": "req-123"
          },
          {
            "key": "X-Correlation-Id",
            "value": "corr-456"
          },
          {
            "key": "X-Consumer",
            "value": "postman"
          }
        ],
        "url": {
          "raw": "{{base_url}}/api/v1/shipments/SHP-REPLACE-ME/history",
          "host": [
            "{{base_url}}"
          ],
          "path": [
            "api",
            "v1",
            "shipments",
            "SHP-REPLACE-ME",
            "history"
          ]
        }
      },
      "response": []
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://127.0.0.1:8000"
    }
  ]
}
`
