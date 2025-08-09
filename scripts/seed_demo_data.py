"""Seed the database with demo data.

This script populates the database with a few dummy source items,
analyses and posts across all topics. It simulates the pipeline
operations by calling the tasks synchronously.

Usage::

    python scripts/seed_demo_data.py
"""

import datetime

from common.database import init_db, SessionLocal
from common.models import TopicEnum
from ingestor.tasks import run as ingest_run
from analyst.tasks import build_analysis
from verifier.tasks import verify_analysis
from post_builder.tasks import build_post


def main() -> None:
    # Initialise tables (for local runs)
    init_db()
    # For each topic ingest one item
    for topic in TopicEnum:
        res = ingest_run.apply(args=[topic.value, 6]).get()
        source_id = res["source_id"]
        # Build analysis
        analysis_res = build_analysis.apply(args=[topic.value, [source_id]]).get()
        analysis_id = analysis_res["analysis_id"]
        # Verify analysis
        verify_analysis.apply(args=[analysis_id]).get()
        # Build post
        post_res = build_post.apply(args=[analysis_id]).get()
        print(f"Created post {post_res['post_id']} for topic {topic.value}")


if __name__ == "__main__":
    main()