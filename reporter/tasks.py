"""Celery tasks for generating daily reports and alerts.

This stub produces no real report but demonstrates how a scheduled
task could be implemented. In a production setting you would query
Prometheus or your application database to derive metrics and send
alerts via email or messaging services.
"""

from typing import Any, Dict

from celery.utils.log import get_task_logger

from common.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="reporter.daily_report")
def daily_report() -> Dict[str, Any]:
    """Stub daily reporting task."""
    logger.info("Running daily report (stub)")
    return {"status": "report_sent"}