"""Add full-text search capability for hybrid search.

Revision ID: 004
Revises: 003
Create Date: 2026-01-12

This migration adds:
1. search_vector tsvector column on scriptures table
2. GIN index for fast full-text search
3. Trigger to auto-update search_vector on insert/update
4. Populates search_vector for existing rows
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tsvector column for full-text search
    op.add_column(
        "scriptures",
        sa.Column("search_vector", sa.dialects.postgresql.TSVECTOR, nullable=True),
    )

    # Create GIN index for fast full-text search
    op.execute("""
        CREATE INDEX idx_scriptures_search_vector
        ON scriptures
        USING GIN (search_vector)
    """)

    # Create function to generate search vector
    # Uses 'english' config for English scriptures
    # Cast to regconfig for PostgreSQL full-text search
    op.execute("""
        CREATE OR REPLACE FUNCTION scriptures_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector(
                (CASE WHEN NEW.lang = 'es' THEN 'spanish' ELSE 'english' END)::regconfig,
                COALESCE(NEW.text, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to auto-update search_vector
    op.execute("""
        CREATE TRIGGER scriptures_search_vector_trigger
        BEFORE INSERT OR UPDATE OF text, lang
        ON scriptures
        FOR EACH ROW
        EXECUTE FUNCTION scriptures_search_vector_update();
    """)

    # Populate search_vector for existing rows
    # This may take a minute for ~42K rows
    op.execute("""
        UPDATE scriptures
        SET search_vector = to_tsvector(
            (CASE WHEN lang = 'es' THEN 'spanish' ELSE 'english' END)::regconfig,
            COALESCE(text, '')
        )
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS scriptures_search_vector_trigger ON scriptures")
    op.execute("DROP FUNCTION IF EXISTS scriptures_search_vector_update()")
    op.drop_index("idx_scriptures_search_vector", table_name="scriptures")
    op.drop_column("scriptures", "search_vector")
