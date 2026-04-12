from celery import Celery

from app.config import celery_redis_settings

celery_app = Celery(
    "worker",
    broker = celery_redis_settings.BROKER_URL,
    backend = celery_redis_settings.RESULT_BACKEND,
    include=["app.tasks.object_detection"],
)