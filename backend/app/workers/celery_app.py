from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "smart_study",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Ensure task registration when the Celery app module is imported.
from app.workers import tasks  # noqa: F401,E402
