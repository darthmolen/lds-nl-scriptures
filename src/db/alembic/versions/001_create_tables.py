"""Create scriptures and cfm_lessons tables.

Revision ID: 001
Revises:
Create Date: 2025-01-11

Initial migration that:
- Enables pgvector extension
- Creates scriptures table for verse-level scripture data
- Creates cfm_lessons table for Come Follow Me content
- Creates indexes for common query patterns
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension for vector similarity search
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create scriptures table
    op.create_table(
        "scriptures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("volume", sa.String(50), nullable=False, index=True),
        sa.Column("book", sa.String(50), nullable=False, index=True),
        sa.Column("chapter", sa.Integer(), nullable=False),
        sa.Column("verse", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("lang", sa.String(5), nullable=False, index=True),
        sa.Column("footnotes", sa.dialects.postgresql.JSONB()),
        sa.Column("context_text", sa.Text()),
        sa.Column("embedding", Vector(1536)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
        ),
    )

    # Create cfm_lessons table
    op.create_table(
        "cfm_lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False, index=True),
        sa.Column("testament", sa.String(50), index=True),
        sa.Column("lesson_id", sa.String(100), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("date_range", sa.String(100)),
        sa.Column("scripture_refs", sa.ARRAY(sa.Text())),
        sa.Column("content", sa.Text()),
        sa.Column("lang", sa.String(5), nullable=False, index=True),
        sa.Column("embedding", Vector(1536)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
        ),
    )

    # Create composite index for scripture reference lookups
    op.create_index(
        "idx_scriptures_ref",
        "scriptures",
        ["volume", "book", "chapter", "verse", "lang"],
    )

    # Create index for language filtering on scriptures
    op.create_index(
        "idx_scriptures_lang",
        "scriptures",
        ["lang"],
    )

    # Create composite index for CFM year and language queries
    op.create_index(
        "idx_cfm_year_lang",
        "cfm_lessons",
        ["year", "lang"],
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_cfm_year_lang", table_name="cfm_lessons")
    op.drop_index("idx_scriptures_lang", table_name="scriptures")
    op.drop_index("idx_scriptures_ref", table_name="scriptures")

    # Drop tables
    op.drop_table("cfm_lessons")
    op.drop_table("scriptures")

    # Note: We intentionally do NOT drop the vector extension
    # as it may be used by other tables in the database
