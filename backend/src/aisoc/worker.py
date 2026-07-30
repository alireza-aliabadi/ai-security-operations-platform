"""Back-compat Celery entry — prefer `aisoc.workers.celery_app`."""

from aisoc.workers.celery_app import celery_app

__all__ = ["celery_app"]
