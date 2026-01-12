"""Add conference_paragraphs table.

Revision ID: 003
Revises: 002
Create Date: 2025-01-12

Creates the conference_paragraphs table for General Conference talk content
with paragraph-level granularity for semantic search.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conference_paragraphs table
    op.create_table(
        "conference_paragraphs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False, index=True),
        sa.Column("month", sa.String(2), nullable=False),
        sa.Column("session", sa.String(50)),
        sa.Column("talk_uri", sa.String(200), nullable=False),
        sa.Column("talk_title", sa.Text()),
        sa.Column("speaker_name", sa.String(200)),
        sa.Column("speaker_role", sa.String(200)),
        sa.Column("paragraph_num", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("lang", sa.String(5), nullable=False, index=True),
        sa.Column("footnotes", sa.dialects.postgresql.JSONB()),
        sa.Column("scripture_refs", sa.ARRAY(sa.Text())),
        sa.Column("talk_refs", sa.ARRAY(sa.Text())),
        sa.Column("context_text", sa.Text()),
        sa.Column("embedding", Vector(1536)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
        ),
    )

    # Create composite index for conference queries
    op.create_index(
        "idx_conference_year_month_lang",
        "conference_paragraphs",
        ["year", "month", "lang"],
    )

    # Create index for talk lookups
    op.create_index(
        "idx_conference_talk_uri",
        "conference_paragraphs",
        ["talk_uri", "lang"],
    )

    # Create index for speaker queries
    op.create_index(
        "idx_conference_speaker",
        "conference_paragraphs",
        ["speaker_name"],
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_conference_speaker", table_name="conference_paragraphs")
    op.drop_index("idx_conference_talk_uri", table_name="conference_paragraphs")
    op.drop_index("idx_conference_year_month_lang", table_name="conference_paragraphs")

    # Drop table
    op.drop_table("conference_paragraphs")
