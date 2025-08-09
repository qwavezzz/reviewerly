"""Backfill the last 24 hours of news for all topics.

This script triggers the ingestion pipeline for the previous 24 hours
across all configured topics. It is intended to be run manually
when first starting the system or recovering from downtime.
"""

from datetime import timedelta
import datetime

from common.models import TopicEnum
from ingestor.tasks import run as ingest_run


def main() -> None:
    now = datetime.datetime.utcnow()
    window_hours = 24
    for topic in TopicEnum:
        res = ingest_run.apply(args=[topic.value, window_hours]).get()
        print(f"Backfill ingest for topic {topic.value}: source {res['source_id']}")


if __name__ == "__main__":
    main()