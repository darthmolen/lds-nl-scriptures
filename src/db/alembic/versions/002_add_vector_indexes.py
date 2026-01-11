"""Add vector indexes for similarity search.

Revision ID: 002
Revises: 001
Create Date: 2026-01-11

This migration adds IVFFlat indexes on the embedding columns
for efficient approximate nearest neighbor search.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Increase maintenance_work_mem for index creation (requires ~65MB for 42K vectors)
    op.execute("SET maintenance_work_mem = '128MB'")

    # IVFFlat index for scriptures embeddings
    # lists=100 is appropriate for ~42K vectors (sqrt(n) rule of thumb)
    op.execute("""
        CREATE INDEX idx_scriptures_embedding
        ON scriptures
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # IVFFlat index for CFM lesson embeddings
    # lists=50 is appropriate for ~200 lessons
    op.execute("""
        CREATE INDEX idx_cfm_embedding
        ON cfm_lessons
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 50)
    """)


def downgrade() -> None:
    op.drop_index("idx_cfm_embedding", table_name="cfm_lessons")
    op.drop_index("idx_scriptures_embedding", table_name="scriptures")
