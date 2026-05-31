"""Expand vector dimensions from 1536 to 2000 for text-embedding-3-large.

Revision ID: 006
Revises: 005
Create Date: 2026-01-14

Upgrading from text-embedding-3-small (1536 dims) to text-embedding-3-large (3072 dims)
for improved semantic understanding, particularly for theological inference queries.

This migration:
1. Drops HNSW indexes (required before changing column type)
2. Expands embedding columns from vector(1536) to vector(2000)
3. NULLs all embeddings (must re-embed with new model)
4. Recreates HNSW indexes

Re-embedding cost: ~42K verses × ~150 tokens × $0.13/1M ≈ $0.82
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop HNSW indexes first (required before changing column type)
    op.execute("DROP INDEX IF EXISTS idx_scriptures_embedding")
    op.execute("DROP INDEX IF EXISTS idx_cfm_embedding")

    # NULL embeddings FIRST (can't cast 1536-dim to 3072-dim)
    op.execute("UPDATE scriptures SET embedding = NULL")
    op.execute("UPDATE cfm_lessons SET embedding = NULL")

    # Now change column dimensions: 1536 -> 3072
    op.execute("ALTER TABLE scriptures ALTER COLUMN embedding TYPE vector(2000)")
    op.execute("ALTER TABLE cfm_lessons ALTER COLUMN embedding TYPE vector(2000)")

    # Recreate HNSW indexes (will be empty until re-embedding)
    op.execute("SET maintenance_work_mem = '64MB'")
    op.execute("""
        CREATE INDEX idx_scriptures_embedding
        ON scriptures
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    op.execute("""
        CREATE INDEX idx_cfm_embedding
        ON cfm_lessons
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_scriptures_embedding")
    op.execute("DROP INDEX IF EXISTS idx_cfm_embedding")

    # NULL embeddings (incompatible dimensions)
    op.execute("UPDATE scriptures SET embedding = NULL")
    op.execute("UPDATE cfm_lessons SET embedding = NULL")

    # Revert column dimensions: 3072 -> 1536
    op.execute("ALTER TABLE scriptures ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("ALTER TABLE cfm_lessons ALTER COLUMN embedding TYPE vector(1536)")

    # Recreate HNSW indexes
    op.execute("SET maintenance_work_mem = '64MB'")
    op.execute("""
        CREATE INDEX idx_scriptures_embedding
        ON scriptures
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    op.execute("""
        CREATE INDEX idx_cfm_embedding
        ON cfm_lessons
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
