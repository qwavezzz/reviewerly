"""Initial tables for news portal.

Revision ID: 0001_initial
Revises: 
Create Date: 2023-08-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'source_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.Enum('ecom', 'it', 'o&g', name='topicenum'), nullable=False),
        sa.Column('source_url', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('event_date', sa.DateTime(), nullable=True),
        sa.Column('language', sa.String(length=8), nullable=True),
        sa.Column('author', sa.String(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('hashes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_url')
    )
    op.create_index('idx_source_item_topic_published', 'source_item', ['topic', 'published_at'], unique=False)

    op.create_table(
        'analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('topic', sa.Enum('ecom', 'it', 'o&g', name='topicenum'), nullable=False),
        sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('thesis', sa.Text(), nullable=True),
        sa.Column('impact_market', sa.Text(), nullable=True),
        sa.Column('winners', sa.Text(), nullable=True),
        sa.Column('losers', sa.Text(), nullable=True),
        sa.Column('scenarios', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence', sa.Numeric(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('topic', sa.Enum('ecom', 'it', 'o&g', name='topicenum'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('body_html', sa.Text(), nullable=False),
        sa.Column('summary_tg', sa.Text(), nullable=True),
        sa.Column('seo', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reliability_score', sa.Numeric(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'in_review', 'approved', 'published', name='poststatus'), nullable=False),
        sa.Column('cms_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    op.create_table(
        'fact',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=False),
        sa.Column('quote', sa.Text(), nullable=False),
        sa.Column('fact_normalized', sa.Text(), nullable=True),
        sa.Column('entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence', sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['source_item.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'verification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('analysis_id', sa.Integer(), nullable=False),
        sa.Column('checks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('reliability_score', sa.Numeric(), nullable=True),
        sa.Column('issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('passed', 'flagged', 'failed', name='verificationstatus'), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['analysis.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('analysis_id'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('actor', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('diff', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ts', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['post.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('verification')
    op.drop_table('fact')
    op.drop_table('post')
    op.drop_table('analysis')
    op.drop_index('idx_source_item_topic_published', table_name='source_item')
    op.drop_table('source_item')
    # Drop enums
    op.execute("DROP TYPE IF EXISTS topicenum")
    op.execute("DROP TYPE IF EXISTS poststatus")
    op.execute("DROP TYPE IF EXISTS verificationstatus")