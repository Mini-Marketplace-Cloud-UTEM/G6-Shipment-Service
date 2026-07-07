"""
Worker Outbox → GCP Pub/Sub.

Lee eventos pendientes de la tabla `outbox_events` y los publica
a un tópico de Google Cloud Pub/Sub. Tras la confirmación de GCP,
marca cada evento como PUBLISHED en la base de datos.

Uso:
    python -m app.worker

Variables de entorno requeridas:
    DATABASE_URL          — Conexión a PostgreSQL (Supabase)
    PUBSUB_TOPIC          — Ruta completa del tópico GCP
                            (ej: projects/mi-proyecto/topics/shipment-events)
    GOOGLE_APPLICATION_CREDENTIALS — (opcional) Ruta al JSON de la service account
"""

import json
import logging
import os
import time

from dotenv import load_dotenv
from google.cloud import pubsub_v1
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("outbox-worker")

# ── Configuración de BD ──────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está configurada")
DATABASE_URL = DATABASE_URL.strip()
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Configuración de Pub/Sub ─────────────────────────────────────────────────
PUBSUB_TOPIC = os.environ.get("PUBSUB_TOPIC", "")
POLL_INTERVAL = int(os.environ.get("OUTBOX_POLL_INTERVAL", "5"))  # segundos

publisher = pubsub_v1.PublisherClient() if PUBSUB_TOPIC else None


def publish_pending_events() -> int:
    """Lee eventos PENDING del outbox, los publica a GCP y los marca PUBLISHED.

    Retorna la cantidad de eventos publicados en esta iteración.
    """
    if not publisher or not PUBSUB_TOPIC:
        logger.warning("PUBSUB_TOPIC no configurado — omitiendo publicación")
        return 0

    db = SessionLocal()
    published_count = 0

    try:
        # Leer lote de eventos pendientes (máx 50 por iteración)
        rows = db.execute(
            text(
                "SELECT id, event_type, payload "
                "FROM outbox_events "
                "WHERE status = 'PENDING' "
                "ORDER BY created_at ASC "
                "LIMIT 50"
            )
        ).fetchall()

        if not rows:
            return 0

        logger.info("Procesando %d evento(s) pendiente(s)...", len(rows))

        for row in rows:
            event_id = row[0]
            event_type = row[1]
            payload = row[2]

            # El payload ya es un dict (JSONB). Lo serializamos para Pub/Sub.
            message_data = json.dumps(payload, default=str).encode("utf-8")

            try:
                future = publisher.publish(
                    PUBSUB_TOPIC,
                    data=message_data,
                    eventType=event_type,
                    producer="g6-despacho",
                )
                # Esperar confirmación de GCP (timeout 10s)
                message_id = future.result(timeout=10)

                # Marcar como PUBLISHED
                db.execute(
                    text(
                        "UPDATE outbox_events SET status = 'PUBLISHED' WHERE id = :eid"
                    ),
                    {"eid": event_id},
                )
                db.commit()
                published_count += 1
                correlation = payload.get("correlationId", "N/A")
                logger.info(
                    "✓ Evento #%d (%s) publicado — message_id=%s [corr_id: %s]",
                    event_id,
                    event_type,
                    message_id,
                    correlation
                )

            except Exception as pub_err:
                db.rollback()
                logger.error(
                    "✗ Error publicando evento #%d (%s): %s",
                    event_id,
                    event_type,
                    pub_err,
                )

    except Exception as db_err:
        logger.error("Error leyendo outbox_events: %s", db_err)
    finally:
        db.close()

    return published_count


def main():
    """Loop principal del worker. Corre indefinidamente con polling."""
    logger.info("═══════════════════════════════════════════════════════")
    logger.info("  Outbox Worker — GCP Pub/Sub")
    logger.info("  Tópico: %s", PUBSUB_TOPIC or "(NO CONFIGURADO)")
    logger.info("  Intervalo de polling: %ds", POLL_INTERVAL)
    logger.info("═══════════════════════════════════════════════════════")

    while True:
        try:
            count = publish_pending_events()
            if count > 0:
                logger.info("Iteración completada: %d evento(s) publicados", count)
        except KeyboardInterrupt:
            logger.info("Worker detenido por el usuario.")
            break
        except Exception as loop_err:
            logger.error("Error en iteración del worker: %s", loop_err)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
