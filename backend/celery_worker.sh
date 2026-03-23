#!/bin/bash
# Start Celery worker for background tasks

echo "🚀 Starting Celery worker..."
echo "📍 Broker: $CELERY_BROKER_URL"
echo "📍 Backend: $CELERY_RESULT_BACKEND"

celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=notifications,default \
    --max-tasks-per-child=100
