"""
Celery application for background tasks
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "attendance_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.notifications",
    ]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Maseru",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Task routes - FIXED: Use actual task names (without module path)
celery_app.conf.task_routes = {
    "send_sms_task": {"queue": "notifications"},
    "send_email_task": {"queue": "notifications"},
    "send_bulk_sms_task": {"queue": "notifications"},
}
