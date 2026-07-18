from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "paperqa",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)
# Ensures tasks defined in app.services.tasks get registered with this app
celery_app.autodiscover_tasks(["app.services"])