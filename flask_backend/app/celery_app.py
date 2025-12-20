import os
from celery import Celery


def make_celery(app_name=__name__):
    broker = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", broker)
    celery = Celery(app_name, broker=broker, backend=backend)
    celery.conf.update(task_track_started=True)
    return celery


celery = make_celery()
