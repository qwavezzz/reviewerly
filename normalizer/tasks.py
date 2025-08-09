"""Celery tasks for normalising raw news content.

The normaliser cleans HTML and extracts structured information such as
named entities. This simplified implementation does nothing beyond
logging. In a production system you would integrate an NLP pipeline
here.
"""

from typing import Any, Dict

from celery.utils.log import get_task_logger

from common.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="normalizer.normalize")
def normalize_source(source_id: int) -> Dict[str, Any]:
    """Stub normalisation task."""
    logger.info("Normalising source_id=%s", source_id)
    # In real life perform cleaning, language detection, NER, etc.
    return {"source_id": source_id, "status": "normalised"}