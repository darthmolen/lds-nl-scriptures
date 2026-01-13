"""Core vector search functionality using pgvector.

This module provides the foundational vector similarity search logic
used by all search services (scriptures, CFM, conference talks).

Supports both pure vector search and hybrid search (vector + full-text).
"""

from typing import Any

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session


# Default hybrid search weight: 0.7 for vector, 0.3 for text
DEFAULT_VECTOR_WEIGHT = 0.7


def execute_vector_search(
    session: Session,
    table: str,
    query_embedding: list[float],
    lang: str,
    limit: int,
    select_columns: str = "*",
    additional_filters: str = "",
    filter_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute a pgvector similarity search.

    Uses cosine distance (<=> operator) for semantic similarity matching.
    Returns similarity as 1 - distance for intuitive 0-1 scoring.

    Note: When additional_filters are provided, we increase ivfflat.probes
    to ensure the IVFFlat index returns results even when filtering reduces
    the candidate set significantly.

    Args:
        session: SQLAlchemy database session
        table: Name of the table to search
        query_embedding: Query vector (1536 dimensions)
        lang: Language code ('en' or 'es')
        limit: Maximum number of results
        select_columns: Columns to select (default: "*")
        additional_filters: Optional SQL WHERE clause additions
        filter_params: Parameters for additional_filters

    Returns:
        List of result dictionaries with similarity scores

    Example:
        results = execute_vector_search(
            session=db,
            table="scriptures",
            query_embedding=embedding,
            lang="en",
            limit=10,
            select_columns="id, book, chapter, verse, text",
            additional_filters="AND volume = :volume",
            filter_params={"volume": "bookofmormon"}
        )
    """
    # Note: With HNSW index, no probes tuning needed (was required for IVFFlat)

    # Build the base query
    # Use CAST instead of :: to avoid SQLAlchemy parameter parsing issues
    base_query = f"""
        SELECT {select_columns},
               1 - (embedding <=> CAST(:query_embedding AS vector)) as similarity
        FROM {table}
        WHERE embedding IS NOT NULL
          AND lang = :lang
          {additional_filters}
        ORDER BY embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
    """

    # Build parameters
    params = {
        "query_embedding": str(query_embedding),
        "lang": lang,
        "limit": limit,
    }
    if filter_params:
        params.update(filter_params)

    # Execute query
    result = session.execute(sql_text(base_query), params)

    # Convert to list of dictionaries
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]


def execute_hybrid_search(
    session: Session,
    table: str,
    query_embedding: list[float],
    query_text: str,
    lang: str,
    limit: int,
    select_columns: str = "*",
    additional_filters: str = "",
    filter_params: dict[str, Any] | None = None,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
) -> list[dict[str, Any]]:
    """Execute hybrid search combining vector similarity and full-text search.

    Combines semantic similarity (pgvector cosine distance) with lexical
    matching (PostgreSQL full-text search) using weighted scoring:

        hybrid_score = vector_weight * vector_similarity + (1 - vector_weight) * text_rank

    This approach helps find results that:
    - Match semantically (vector search)
    - Contain exact terms like "liahona", "Urim and Thummim" (text search)

    Args:
        session: SQLAlchemy database session
        table: Name of the table to search (must have search_vector column)
        query_embedding: Query vector (1536 dimensions)
        query_text: Original query text for full-text search
        lang: Language code ('en' or 'es')
        limit: Maximum number of results
        select_columns: Columns to select (default: "*")
        additional_filters: Optional SQL WHERE clause additions
        filter_params: Parameters for additional_filters
        vector_weight: Weight for vector similarity (0-1), text gets 1-weight

    Returns:
        List of result dictionaries with hybrid_score

    Example:
        results = execute_hybrid_search(
            session=db,
            table="scriptures",
            query_embedding=embedding,
            query_text="liahona compass",
            lang="en",
            limit=10,
        )
    """
    # Note: With HNSW index, no probes tuning needed (was required for IVFFlat)

    # Text weight is complement of vector weight
    text_weight = 1.0 - vector_weight

    # Choose text search config based on language
    ts_config = "spanish" if lang == "es" else "english"

    # Convert query text to OR-based tsquery
    # Split on whitespace and punctuation, filter empty, join with |
    import re
    words = re.split(r'[\s,;:.!?]+', query_text.lower())
    words = [w.strip() for w in words if w.strip() and len(w.strip()) > 2]
    # Create OR query: word1 | word2 | word3
    or_query = " | ".join(words) if words else query_text

    # Hybrid search query:
    # 1. Get candidate IDs from both vector search and text search
    # 2. Compute BOTH scores for ALL candidates (not just the search that found them)
    # 3. Rank by hybrid score
    hybrid_query = f"""
        WITH
        -- Get top candidates from vector search
        vector_candidates AS (
            SELECT id
            FROM {table}
            WHERE embedding IS NOT NULL
              AND lang = :lang
              {additional_filters}
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :search_limit
        ),
        -- Get top candidates from text search
        text_candidates AS (
            SELECT id
            FROM {table},
                 to_tsquery(:ts_config, :or_query) query
            WHERE search_vector @@ query
              AND lang = :lang
              {additional_filters}
            LIMIT :search_limit
        ),
        -- Combine all candidate IDs
        all_candidates AS (
            SELECT id FROM vector_candidates
            UNION
            SELECT id FROM text_candidates
        ),
        -- Compute both scores for ALL candidates
        scored AS (
            SELECT s.{select_columns.replace(', ', ', s.')},
                   1 - (s.embedding <=> CAST(:query_embedding AS vector)) as vec_score,
                   COALESCE(ts_rank_cd(s.search_vector, to_tsquery(:ts_config, :or_query)), 0) as text_score
            FROM {table} s
            JOIN all_candidates c ON s.id = c.id
            WHERE s.embedding IS NOT NULL
        )
        SELECT *,
               vec_score as vector_similarity,
               text_score as text_rank,
               (
                   :vector_weight * vec_score +
                   :text_weight * text_score
               ) as hybrid_score
        FROM scored
        ORDER BY hybrid_score DESC
        LIMIT :limit
    """

    # Build parameters
    params = {
        "query_embedding": str(query_embedding),
        "or_query": or_query,
        "ts_config": ts_config,
        "lang": lang,
        "limit": limit,
        "search_limit": limit * 3,  # Fetch more candidates for merging
        "vector_weight": vector_weight,
        "text_weight": text_weight,
    }
    if filter_params:
        params.update(filter_params)

    # Execute query
    result = session.execute(sql_text(hybrid_query), params)

    # Convert to list of dictionaries
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]
