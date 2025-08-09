"""Celery tasks for ingesting raw news data from external sources.

This module defines a task that queries the configured research
provider (e.g. Perplexity) for the latest events in a given topic
window. For the purposes of this skeleton implementation, the task
generates a single fake ``SourceItem`` entry in the database with
placeholder data. In a real system you would implement calls to the
provider here.
"""

import datetime
from typing import Any, Dict

from celery.utils.log import get_task_logger

from common.celery_app import celery_app
from common.database import SessionLocal
from common.models import SourceItem, TopicEnum


logger = get_task_logger(__name__)


@celery_app.task(name="ingestor.run")
def run(topic: str, window_hours: int = 6) -> Dict[str, Any]:
    """Ingest the latest sources for a given topic.

    :param topic: The topic to ingest (e.g. "it", "ecom", "o&g").
    :param window_hours: Lookback window in hours.
    :returns: A dict summarising the ingestion results.
    """
    logger.info("Starting ingestion for topic=%s window=%s", topic, window_hours)
    session = SessionLocal()
    try:
        # In a real implementation we would call an external service (e.g.
        # Perplexity) here and parse its response into SourceItem
        # instances. For demonstration we create a single dummy item.
        now = datetime.datetime.utcnow()
        source = SourceItem(
            topic=TopicEnum(topic),
            source_url=f"https://example.com/{topic}/{int(now.timestamp())}",
            domain="example.com",
            title=f"Пример новости по теме {topic}",
            excerpt="Краткий обзор события.",
            # Use a single‑line placeholder; multi‑line text would be normalised
            # in the normaliser service.
            content=(
                "Полный текст новости, который будет очищен и нормализован."
            ),
            published_at=now,
            event_date=now - datetime.timedelta(hours=1),
            language="ru",
            author="Unknown",
            fetched_at=now,
            hashes={"title_hash": "abcdef", "content_shingle": "ghijkl"},
        )
        session.add(source)
        session.commit()
        session.refresh(source)
        logger.info("Ingested source_item id=%s", source.id)
        return {"status": "completed", "source_id": source.id}
    except Exception as exc:  # noqa: B902
        session.rollback()
        logger.exception("Ingestion failed: %s", exc)
        raise
    finally:
        session.close()