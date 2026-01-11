#!/usr/bin/env python3
"""Verify embedding generation and test semantic search."""
import os
from sqlalchemy import text as sql_text

from src.db import get_session
from src.db.models import Scripture
from src.embeddings.client import get_single_embedding


def verify_embedding_counts(session):
    """Check how many verses have embeddings."""
    print("\n=== Embedding Counts ===")

    result = session.execute(sql_text("""
        SELECT lang,
               COUNT(*) as total,
               COUNT(embedding) as with_embedding,
               COUNT(*) - COUNT(embedding) as missing
        FROM scriptures
        GROUP BY lang
        ORDER BY lang
    """))

    for row in result:
        pct = (row.with_embedding / row.total * 100) if row.total > 0 else 0
        print(f"  {row.lang}: {row.with_embedding:,}/{row.total:,} ({pct:.1f}%) - {row.missing:,} missing")


def verify_embedding_dimensions(session):
    """Verify embedding dimensions are correct (1536)."""
    print("\n=== Embedding Dimensions ===")

    result = session.execute(sql_text("""
        SELECT vector_dims(embedding) as dims
        FROM scriptures
        WHERE embedding IS NOT NULL
        LIMIT 1
    """))

    row = result.fetchone()
    if row:
        dims = row.dims
        expected = 1536
        status = "OK" if dims == expected else f"WRONG (expected {expected})"
        print(f"  Dimensions: {dims} - {status}")
    else:
        print("  No embeddings found to check")


def test_semantic_search(session, query: str, limit: int = 5):
    """Test semantic search with a query."""
    print(f"\n=== Semantic Search: '{query}' ===")

    # Get embedding for query
    query_embedding = get_single_embedding(query)

    # Search for similar verses
    # Use CAST instead of :: to avoid SQLAlchemy parameter parsing issues
    result = session.execute(sql_text("""
        SELECT book, chapter, verse, lang,
               LEFT(text, 80) as text_preview,
               1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
        FROM scriptures
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
    """), {"query_embedding": str(query_embedding), "limit": limit})

    for i, row in enumerate(result, 1):
        print(f"\n  {i}. {row.book} {row.chapter}:{row.verse} ({row.lang})")
        print(f"     Similarity: {row.similarity:.4f}")
        print(f"     {row.text_preview}...")


def verify_cfm_embeddings(session):
    """Check CFM lesson embedding status."""
    print("\n=== CFM Lesson Embeddings ===")

    result = session.execute(sql_text("""
        SELECT lang, year,
               COUNT(*) as total,
               COUNT(embedding) as with_embedding
        FROM cfm_lessons
        GROUP BY lang, year
        ORDER BY year, lang
    """))

    for row in result:
        pct = (row.with_embedding / row.total * 100) if row.total > 0 else 0
        print(f"  {row.year} {row.lang}: {row.with_embedding}/{row.total} ({pct:.0f}%)")


def main():
    print("Starting embedding verification...")

    with get_session() as session:
        verify_embedding_counts(session)
        verify_embedding_dimensions(session)
        verify_cfm_embeddings(session)

        # Only run semantic search if we have embeddings and API key
        if os.getenv("AZURE_OPENAI_API_KEY"):
            test_semantic_search(session, "faith in Jesus Christ")
            test_semantic_search(session, "love one another")
        else:
            print("\n=== Skipping semantic search (no API key) ===")

    print("\n=== Verification Complete ===")


if __name__ == "__main__":
    main()
