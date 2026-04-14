"""
Celery application instance.

Uses Redis as both broker and result backend. Two separate Redis DBs keep
Celery's queues/results isolated from the app's cache:
  - DB 0  app cache (get_cached / set_cached)
  - DB 1  Celery broker + result backend  ← this file

Usage:
    # start the worker (Docker Compose does this automatically):
    celery -A app.worker worker --loglevel=info

    # from application code — import celery_app and use .delay():
    from app.worker import celery_app
"""

from celery import Celery

from app.config import settings

# Strip any trailing slash then append the Redis DB index
_base_url = settings.redis_url.rstrip("/")
_celery_url = f"{_base_url}/1"   # DB 1 — separate from app cache on DB 0

celery_app = Celery(
    "codelens",
    broker=_celery_url,
    backend=_celery_url,
    include=["app.tasks.review"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,          # auto-expire results after 1 hour (matches cache TTL)
    task_track_started=True,      # STARTED state visible via AsyncResult.state
    worker_prefetch_multiplier=1, # one task at a time per worker — LLM calls are slow
)
