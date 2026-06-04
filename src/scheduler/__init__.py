"""Batch Scheduler Module.

Handles task queuing, batch submission, and adaptive concurrency control.
"""

from .celery_app import celery_app

__all__ = ["celery_app"]