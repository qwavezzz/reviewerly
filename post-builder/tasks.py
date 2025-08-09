"""Celery tasks for building posts from analyses.

This module contains logic to transform an ``Analysis`` record (and its
associated ``Verification``) into a publishable ``Post``. The long
version is rendered as HTML using a Jinja2 template while the short
version (Telegram) is created as plain text with bullet points. SEO
metadata is derived from the analysis content.

In a production system the templates would live in separate files
under the ``post-builder/templates`` directory; here we embed them
inline for brevity.
"""

import datetime
import re
from typing import Any, Dict

from celery.utils.log import get_task_logger
from jinja2 import Environment, BaseLoader

from common.celery_app import celery_app
from common.database import SessionLocal
from common.models import Analysis, Post, TopicEnum, PostStatus, Verification


logger = get_task_logger(__name__)


LONG_TEMPLATE = """
<h2>{{ title }}</h2>
<p><strong>TL;DR:</strong></p>
<ul>
{% for bullet in tldr %}
  <li>{{ bullet }}</li>
{% endfor %}
</ul>
<h3>Что произошло</h3>
<p>{{ thesis }}</p>
<h3>Почему важно рынку</h3>
<p>{{ impact }}</p>
<h3>Кто выигрывает / проигрывает</h3>
<p><strong>Выигрывают:</strong> {{ winners }}</p>
<p><strong>Проигрывают:</strong> {{ losers }}</p>
<h3>Сценарии 1–3 месяца</h3>
<ul>
{% for sc in scenarios %}
  <li>{{ sc.case }} ({{ sc.likelihood*100|round(0) }}%): {{ sc.text }}</li>
{% endfor %}
</ul>
<h3>Риски и что мониторить</h3>
<ul>
{% for risk in risks %}
  <li>{{ risk }}</li>
{% endfor %}
</ul>
<p><em>Дисклеймер: материал — общая информация, не персональный инвестсовет.</em></p>
"""


def slugify(value: str) -> str:
    """Generate a URL‑friendly slug from a string."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9\-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


@celery_app.task(name="post_builder.build")
def build_post(analysis_id: int) -> Dict[str, Any]:
    """Generate a post from an analysis.

    :param analysis_id: ID of the analysis to build a post for.
    :returns: A dict containing the post ID.
    """
    session = SessionLocal()
    try:
        analysis = session.get(Analysis, analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        # Retrieve verification for reliability score
        verification = session.query(Verification).filter_by(analysis_id=analysis_id).one_or_none()
        reliability_score = verification.reliability_score if verification else None
        # Compose title (simple for demo)
        event_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        title = f"Аналитика по теме {analysis.topic.value.upper()} — {event_date}"
        # Prepare TL;DR bullets (first lines of sections)
        tldr = [
            analysis.thesis or "нет тезиса",
            analysis.impact_market or "нет влияния",
            f"Выигрывают: {analysis.winners or 'нет данных'}; Проигрывают: {analysis.losers or 'нет данных'}",
        ]
        # Render long HTML
        env = Environment(loader=BaseLoader(), autoescape=True)
        template = env.from_string(LONG_TEMPLATE)
        body_html = template.render(
            title=title,
            tldr=tldr,
            thesis=analysis.thesis,
            impact=analysis.impact_market,
            winners=analysis.winners,
            losers=analysis.losers,
            scenarios=analysis.scenarios or [],
            risks=analysis.risks or [],
        )
        # Short summary for Telegram
        summary_tg = f"{title}\n\n" + "\n".join([f"• {b}" for b in tldr]) + "\n\nПолная аналитика → {link}"
        # Generate slug
        slug = slugify(f"{analysis.topic.value}-{analysis.id}-{event_date}")
        # SEO metadata
        seo = {
            "title": title[:60],
            "description": (analysis.thesis or "")[:155],
            "keywords": [analysis.topic.value],
            "og_image": None,
            "schema": {
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": title,
                "datePublished": event_date,
                "dateModified": event_date,
            },
        }
        post = Post(
            slug=slug,
            topic=analysis.topic,
            title=title,
            body_html=body_html,
            summary_tg=summary_tg,
            seo=seo,
            sources=analysis.items,
            reliability_score=reliability_score,
            status=PostStatus.DRAFT,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
        )
        session.add(post)
        session.commit()
        session.refresh(post)
        logger.info("Built post id=%s from analysis=%s", post.id, analysis.id)
        return {"post_id": post.id}
    except Exception as exc:
        session.rollback()
        logger.exception("Post build failed: %s", exc)
        raise
    finally:
        session.close()