from celery import Celery
from shared.config import get_settings


settings = get_settings()

app = Celery(
    "batch_processing_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["batch_processing_service.tasks"],
)


@app.task
def ping() -> str:
    return "pong"
