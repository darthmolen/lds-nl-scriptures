"""Come Follow Me (CFM) lesson search service.

This module provides CFM-specific search functionality,
building on the core vector search with year and testament filters.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.api.services.search import execute_vector_search


def search_cfm_lessons(
    session: Session,
    query_embedding: list[float],
    lang: str,
    limit: int,
    year: Optional[int] = None,
    testament: Optional[str] = None,
) -> list[dict]:
    """Search CFM lessons by semantic similarity.

    Performs a vector similarity search against the cfm_lessons table,
    optionally filtered by year and/or testament.

    Args:
        session: SQLAlchemy database session
        query_embedding: Query vector (1536 dimensions)
        lang: Language code ('en' or 'es')
        limit: Maximum number of results
        year: Optional year filter (e.g., 2024)
        testament: Optional testament filter ('ot', 'nt', 'bom', 'dc')

    Returns:
        List of CFM lesson result dictionaries with content_preview
    """
    # Build optional filters
    additional_filters = ""
    filter_params = {}

    if year:
        additional_filters += " AND year = :year"
        filter_params["year"] = year

    if testament:
        additional_filters += " AND testament = :testament"
        filter_params["testament"] = testament

    # Execute search
    results = execute_vector_search(
        session=session,
        table="cfm_lessons",
        query_embedding=query_embedding,
        lang=lang,
        limit=limit,
        select_columns="id, year, testament, lesson_id, title, date_range, scripture_refs, content, lang",
        additional_filters=additional_filters,
        filter_params=filter_params,
    )

    # Format results with content_preview (first 500 chars)
    formatted_results = []
    for row in results:
        content = row.get("content") or ""
        content_preview = content[:500] if len(content) > 500 else content

        formatted_results.append({
            "id": row["id"],
            "year": row["year"],
            "testament": row["testament"],
            "lesson_id": row["lesson_id"],
            "title": row["title"],
            "date_range": row["date_range"],
            "scripture_refs": row["scripture_refs"],
            "content_preview": content_preview,
            "lang": row["lang"],
            "similarity": round(row["similarity"], 4),
        })

    return formatted_results
