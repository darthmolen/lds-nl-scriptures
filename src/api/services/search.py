"""Core vector search functionality using pgvector.

This module provides the foundational vector similarity search logic
used by all search services (scriptures, CFM, conference talks).
"""

from typing import Any

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session


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
    # When using filters with IVFFlat index, increase probes to ensure
    # we find matching results even when filter reduces candidate set
    if additional_filters:
        session.execute(sql_text("SET ivfflat.probes = 100"))

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
