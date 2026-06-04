"""Celery application configuration for batch task scheduling."""

from celery import Celery

from src.common.config import get_settings

settings = get_settings()

celery_app = Celery(
    "autotest-agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.scheduler.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=settings.sandbox_timeout,
    task_time_limit=settings.sandbox_timeout + 60,
)