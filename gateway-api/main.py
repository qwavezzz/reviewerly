"""Gateway API service.

This FastAPI application exposes a REST interface for orchestrating
the news ingestion and analysis pipeline. Clients (e.g. the editor
console) interact with this service to trigger ingest runs, build
analyses and posts, approve or publish posts, and list drafts.
"""

from __future__ import annotations

import os
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from celery.result import AsyncResult

from common.database import SessionLocal
from common.models import Post, PostStatus, TopicEnum

from ingestor.tasks import run as ingest_run
from analyst.tasks import build_analysis
from verifier.tasks import verify_analysis
from post_builder.tasks import build_post
from publisher.tasks import publish_post


app = FastAPI(
    title="News Portal Gateway API",
    version="1.0.0",
    description="API для управления процессом сбора, анализа и публикации новостей.",
)

# Allow all origins for simplicity; adjust for production use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get a database session per request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class IngestRequest(BaseModel):
    topic: TopicEnum
    window_hours: int = Field(6, ge=1, le=48)


class IngestResponse(BaseModel):
    job_id: str


@app.post("/v1/ingest/run", response_model=IngestResponse)
def ingest_run_endpoint(req: IngestRequest) -> IngestResponse:
    """Trigger ingestion of raw sources for a topic and time window."""
    res = ingest_run.delay(req.topic.value, req.window_hours)
    return IngestResponse(job_id=res.id)


class AnalysisRequest(BaseModel):
    topic: TopicEnum
    source_ids: List[int]


class AnalysisResponse(BaseModel):
    analysis_id: int


@app.post("/v1/analysis/build", response_model=AnalysisResponse)
def analysis_build_endpoint(req: AnalysisRequest) -> AnalysisResponse:
    """Start building an analysis from existing sources."""
    res = build_analysis.delay(req.topic.value, req.source_ids)
    # Wait for result briefly or return job ID (simplified: we block until result)
    result = res.get(timeout=30)
    analysis_id = result.get("analysis_id")
    # Immediately queue verification
    verify_analysis.delay(analysis_id)
    return AnalysisResponse(analysis_id=analysis_id)


class PostBuildRequest(BaseModel):
    analysis_id: int


class PostBuildResponse(BaseModel):
    post_id: int


@app.post("/v1/post/build", response_model=PostBuildResponse)
def post_build_endpoint(req: PostBuildRequest) -> PostBuildResponse:
    """Generate a post from an analysis."""
    res = build_post.delay(req.analysis_id)
    result = res.get(timeout=30)
    post_id = result.get("post_id")
    return PostBuildResponse(post_id=post_id)


class ApproveRequest(BaseModel):
    post_id: int


@app.post("/v1/post/approve")
def post_approve_endpoint(req: ApproveRequest, db=Depends(get_db)) -> dict:
    """Mark a post as approved for publication."""
    post: Optional[Post] = db.get(Post, req.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.status = PostStatus.APPROVED
    db.commit()
    return {"status": "approved", "post_id": post.id}


class PublishRequest(BaseModel):
    post_id: int
    channels: List[str] = Field(..., example=["cms", "telegram"])


@app.post("/v1/post/publish")
def post_publish_endpoint(req: PublishRequest) -> dict:
    """Publish a post to the requested channels."""
    res = publish_post.delay(req.post_id, req.channels)
    result = res.get(timeout=60)
    return result


@app.get("/v1/editor/drafts")
def list_drafts(
    status: PostStatus = Query(PostStatus.IN_REVIEW, description="Статус черновиков"),
    min_score: float = Query(0, ge=0, le=100, description="Минимальный надёжный балл"),
    db=Depends(get_db),
) -> List[dict]:
    """List draft posts filtered by status and reliability score."""
    posts = (
        db.query(Post)
        .filter(Post.status == status)
        .filter((Post.reliability_score >= min_score) | (Post.reliability_score == None))
        .order_by(Post.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "reliability_score": float(p.reliability_score) if p.reliability_score else None,
            "created_at": p.created_at.isoformat(),
            "status": p.status.value,
        }
        for p in posts
    ]