"""Celery tasks for generating analytical reports using GPT‑5.

This simplified implementation synthesises analysis records from
previously ingested and normalised sources. It does not call any LLM
provider but instead constructs deterministic dummy content for
demonstration purposes. Real implementations would make API calls to
OpenAI or similar and parse the responses according to the defined
prompts.
"""

import datetime
from typing import Any, Dict, List

from celery.utils.log import get_task_logger

from common.celery_app import celery_app
from common.database import SessionLocal
from common.models import Analysis, TopicEnum

logger = get_task_logger(__name__)


@celery_app.task(name="analyst.build")
def build_analysis(topic: str, source_ids: List[int]) -> Dict[str, Any]:
    """Construct an analysis from a set of source identifiers.

    :param topic: The analysis topic.
    :param source_ids: List of source_item IDs that form the input.
    :returns: A summary with the new analysis ID.
    """
    logger.info("Building analysis for topic=%s with %d sources", topic, len(source_ids))
    session = SessionLocal()
    try:
        scenarios = [
            {
                "horizon": "1m",
                "case": "base",
                "likelihood": 0.6,
                "text": "Основной сценарий: рынок остаётся стабильным на фоне текущих событий.",
            },
            {
                "horizon": "1m",
                "case": "bull",
                "likelihood": 0.25,
                "text": "Позитивный сценарий: спрос растёт, выигрывают лидеры отрасли.",
            },
            {
                "horizon": "1m",
                "case": "bear",
                "likelihood": 0.15,
                "text": "Негативный сценарий: регуляторные риски и снижение маржи давят на рынок.",
            },
        ]
        analysis = Analysis(
            topic=TopicEnum(topic),
            items={"source_ids": source_ids},
            thesis="Сводка ключевых событий и их влияния на отрасль.",
            impact_market="Умеренное влияние на рынок с потенциалом роста.",
            winners="Крупные публичные компании, эффективно управляющие затратами.",
            losers="Малые игроки с высокой долговой нагрузкой.",
            scenarios=scenarios,
            risks=["Рост процентных ставок", "Политические ограничения"],
            confidence=0.75,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(analysis)
        session.commit()
        session.refresh(analysis)
        logger.info("Created analysis id=%s", analysis.id)
        return {"analysis_id": analysis.id, "status": "completed"}
    except Exception as exc:  # noqa: B902
        session.rollback()
        logger.exception("Analysis failed: %s", exc)
        raise
    finally:
        session.close()