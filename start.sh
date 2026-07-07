#!/bin/bash

# Iniciar el worker de Pub/Sub en segundo plano
echo "Iniciando Outbox Worker en segundo plano..."
python -m app.worker &

# Iniciar la API de FastAPI en primer plano
echo "Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
