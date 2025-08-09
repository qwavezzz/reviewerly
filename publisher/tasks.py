"""Celery tasks for publishing posts to external channels.

This module implements simple adapters for publishing a post to a CMS
and to Telegram. Real implementations would talk to the Ghost Admin
API, WordPress REST API or the Telegram Bot API. Here we log the
actions and update the post status accordingly.
"""

import os
from typing import Any, Dict, List

from celery.utils.log import get_task_logger
import requests

from common.celery_app import celery_app
from common.database import SessionLocal
from common.models import Post, PostStatus

logger = get_task_logger(__name__)


def _post_to_cms(post: Post) -> str:
    """Stub to publish a post to Ghost/WordPress.

    Returns the CMS ID of the created/updated post.
    """
    cms_provider = os.getenv("CMS_PROVIDER", "ghost")
    # In a real implementation, you'd call the provider API here.
    logger.info("Publishing post %s to CMS provider %s", post.slug, cms_provider)
    return f"cms-{post.slug}"


def _post_to_telegram(post: Post) -> None:
    """Stub to publish a post summary to Telegram via Bot API."""
    telegram_token = os.getenv("TELEGRAM_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not telegram_token or not chat_id:
        logger.warning("Telegram credentials not configured; skipping Telegram publishing")
        return
    message = post.summary_tg.replace("{link}", f"https://example.com/{post.slug}")
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if not resp.ok:
            logger.error("Telegram API responded with status %s: %s", resp.status_code, resp.text)
        else:
            logger.info("Sent post %s to Telegram", post.slug)
    except Exception as exc:
        logger.exception("Failed to send post to Telegram: %s", exc)


@celery_app.task(name="publisher.publish")
def publish_post(post_id: int, channels: List[str]) -> Dict[str, Any]:
    """Publish a post to the specified channels.

    :param post_id: The ID of the post to publish.
    :param channels: A list of channels, e.g. ["cms", "telegram"].
    :returns: A dict with publication details.
    """
    session = SessionLocal()
    try:
        post = session.get(Post, post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found")
        # Publish to CMS
        cms_id = None
        if "cms" in channels:
            cms_id = _post_to_cms(post)
            post.cms_id = cms_id
        # Publish to Telegram
        if "telegram" in channels:
            _post_to_telegram(post)
        post.status = PostStatus.PUBLISHED
        session.commit()
        logger.info("Published post %s to channels %s", post.slug, channels)
        return {"post_id": post.id, "cms_id": cms_id, "status": post.status.value}
    except Exception as exc:
        session.rollback()
        logger.exception("Publishing failed: %s", exc)
        raise
    finally:
        session.close()