"""Celery tasks for deduplicating sources.

This module demonstrates a placeholder deduper. Real implementations
would compute shingles or hashes and compare them to recently ingested
records. When a duplicate is detected, processing of that source can
be skipped.
"""

from typing import Any, Dict

from celery.utils.log import get_task_logger

from common.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="deduper.check")
def dedupe_source(source_id: int) -> Dict[str, Any]:
    """Stub deduplication task."""
    logger.info("Checking for duplicates: source_id=%s", source_id)
    # Pretend there is no duplicate
    return {"source_id": source_id, "is_duplicate": False}