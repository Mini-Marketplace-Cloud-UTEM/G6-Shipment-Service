erDiagram
    shipments ||--o{ shipment_status_history : "registra cambios en"
    
    shipments {
        TEXT shipment_id PK
        TEXT order_id
        TEXT customer_name
        TEXT address
        TEXT city
        TEXT origin_cd
        REAL volumetric_weight
        INTEGER shipping_cost
        REAL weight_kg
        TEXT status
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP estimated_delivery
    }

    shipment_status_history {
        SERIAL id PK
        TEXT shipment_id FK
        TEXT status
        TIMESTAMP created_at
    }

    outbox_events {
        SERIAL id PK
        TEXT event_type
        JSONB payload
        TEXT status
        TIMESTAMP created_at
    }
