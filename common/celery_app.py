"""Celery application factory.

Each microservice imports the shared Celery instance from this module. The
broker and backend URLs are read from environment variables. When
running under docker‑compose the broker will be provided by the Redis
service.

Usage:

    from common.celery_app import celery_app

    @celery_app.task
    def my_task(...):
        ...

You can then run celery workers with::

    celery -A common.celery_app.celery_app worker -l info

Or for each service you may create a service‑specific worker module that
imports tasks and starts a worker.
"""

import os
from celery import Celery


def create_celery_app() -> Celery:
    """Create and configure a Celery application instance."""
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    backend_url = os.getenv("CELERY_RESULT_BACKEND", broker_url)
    app = Celery(
        "news_portal",
        broker=broker_url,
        backend=backend_url,
        include=[],
    )
    # Set a default serialization format that plays nicely with Python
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        worker_cancel_long_running_tasks_on_connection_loss=True,
    )
    return app


# Export a singleton Celery app for ease of import.
celery_app = create_celery_app()