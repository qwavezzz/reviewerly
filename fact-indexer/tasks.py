"""Celery tasks for indexing extracted facts into Postgres and OpenSearch.

In this simplified stub we just log the action. A real implementation
would parse the normalised text, run a NER model and store the facts
and their metadata into both PostgreSQL and an OpenSearch index.
"""

from typing import Any, Dict

from celery.utils.log import get_task_logger

from common.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="fact_indexer.index")
def index_facts(source_id: int) -> Dict[str, Any]:
    """Stub fact indexing task."""
    logger.info("Indexing facts for source_id=%s", source_id)
    return {"source_id": source_id, "facts_indexed": 0}