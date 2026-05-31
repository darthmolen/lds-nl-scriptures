"""Switch from IVFFlat to HNSW indexes.

Revision ID: 005
Revises: 004
Create Date: 2026-01-13

HNSW provides better recall than IVFFlat without needing to tune probes.
IVFFlat clusters vectors into lists and can miss results in other clusters.
HNSW builds a navigable graph that naturally finds similar vectors.

For our static ~42K verse dataset, HNSW is the better choice:
- Consistently high recall (no probes tuning)
- Fast queries
- Slightly higher memory (acceptable for our size)
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use moderate maintenance_work_mem for index creation
    # HNSW builds incrementally so doesn't need as much as IVFFlat
    op.execute("SET maintenance_work_mem = '64MB'")

    # Drop IVFFlat indexes
    op.execute("DROP INDEX IF EXISTS idx_scriptures_embedding")
    op.execute("DROP INDEX IF EXISTS idx_cfm_embedding")

    # Create HNSW index for scriptures
    # m=16: connections per node (default, good balance)
    # ef_construction=64: build-time search width (higher = better index, slower build)
    op.execute("""
        CREATE INDEX idx_scriptures_embedding
        ON scriptures
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Create HNSW index for CFM lessons
    op.execute("""
        CREATE INDEX idx_cfm_embedding
        ON cfm_lessons
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    # Revert to IVFFlat indexes
    op.execute("SET maintenance_work_mem = '128MB'")

    op.execute("DROP INDEX IF EXISTS idx_scriptures_embedding")
    op.execute("DROP INDEX IF EXISTS idx_cfm_embedding")

    op.execute("""
        CREATE INDEX idx_scriptures_embedding
        ON scriptures
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    op.execute("""
        CREATE INDEX idx_cfm_embedding
        ON cfm_lessons
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 50)
    """)
