"""SQLAlchemy models for the news portal.

These models represent the core domain entities used throughout the
system. The schema is intentionally denormalised in places (JSONB
columns) to support flexible storage of semi‑structured data such as
entities extracted from text, analysis scenarios and SEO metadata.

Alembic migrations are recommended for managing schema evolution. The
``init_db`` function in :mod:`common.database` can be used to
initialise the tables during local development.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    Enum,
    ForeignKey,
    Text,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base


class TopicEnum(str, enum.Enum):
    """Enumeration of supported topics."""

    ECOM = "ecom"
    IT = "it"
    OG = "o&g"


class VerificationStatus(str, enum.Enum):
    """Enumeration of verification statuses."""

    PASSED = "passed"
    FLAGGED = "flagged"
    FAILED = "failed"


class PostStatus(str, enum.Enum):
    """Enumeration of post lifecycle statuses."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"


class SourceItem(Base):
    __tablename__ = "source_item"

    id = Column(Integer, primary_key=True)
    topic = Column(Enum(TopicEnum), nullable=False)
    source_url = Column(String, nullable=False, unique=True)
    domain = Column(String, nullable=True)
    title = Column(String, nullable=False)
    excerpt = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    event_date = Column(DateTime, nullable=True)
    language = Column(String(8), nullable=True)
    author = Column(String, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    hashes = Column(JSONB, nullable=True)

    # Relationships
    facts = relationship("Fact", back_populates="source", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_source_item_topic_published", "topic", "published_at"),
    )


class Fact(Base):
    __tablename__ = "fact"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("source_item.id", ondelete="CASCADE"), nullable=False)
    quote = Column(Text, nullable=False)
    fact_normalized = Column(Text, nullable=True)
    entities = Column(JSONB, nullable=True)
    confidence = Column(Numeric, nullable=True)

    source = relationship("SourceItem", back_populates="facts")


class Analysis(Base):
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True)
    topic = Column(Enum(TopicEnum), nullable=False)
    items = Column(JSONB, nullable=False)  # e.g. list of source IDs or facts
    thesis = Column(Text, nullable=True)
    impact_market = Column(Text, nullable=True)
    winners = Column(Text, nullable=True)
    losers = Column(Text, nullable=True)
    scenarios = Column(JSONB, nullable=True)  # list of {horizon, case, likelihood, text}
    risks = Column(JSONB, nullable=True)
    confidence = Column(Numeric, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    verification = relationship("Verification", uselist=False, back_populates="analysis", cascade="all, delete-orphan")


class Verification(Base):
    __tablename__ = "verification"

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False, unique=True)
    checks = Column(JSONB, nullable=True)
    reliability_score = Column(Numeric, nullable=True)
    issues = Column(JSONB, nullable=True)
    status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.PASSED)

    analysis = relationship("Analysis", back_populates="verification")


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    topic = Column(Enum(TopicEnum), nullable=False)
    title = Column(String, nullable=False)
    body_html = Column(Text, nullable=False)
    summary_tg = Column(Text, nullable=True)
    seo = Column(JSONB, nullable=True)
    sources = Column(JSONB, nullable=True)
    reliability_score = Column(Numeric, nullable=True)
    status = Column(Enum(PostStatus), nullable=False, default=PostStatus.DRAFT)
    cms_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    logs = relationship("AuditLog", back_populates="post", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    diff = Column(JSONB, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("Post", back_populates="logs")