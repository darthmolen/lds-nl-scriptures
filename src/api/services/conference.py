"""General Conference talk search service.

This module provides conference-specific search functionality,
building on the core vector search with year, month, and speaker filters.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.api.services.search import execute_vector_search


def search_conference_talks(
    session: Session,
    query_embedding: list[float],
    lang: str,
    limit: int,
    year: Optional[int] = None,
    month: Optional[str] = None,
    speaker: Optional[str] = None,
) -> list[dict]:
    """Search conference talks by semantic similarity.

    Performs a vector similarity search against the conference_paragraphs table,
    optionally filtered by year, month, and/or speaker.

    Args:
        session: SQLAlchemy database session
        query_embedding: Query vector (1536 dimensions)
        lang: Language code ('en' or 'es')
        limit: Maximum number of results
        year: Optional year filter (e.g., 2024)
        month: Optional month filter ('04' or '10')
        speaker: Optional speaker name partial match filter

    Returns:
        List of conference paragraph result dictionaries
    """
    # Build optional filters
    additional_filters = ""
    filter_params = {}

    if year:
        additional_filters += " AND year = :year"
        filter_params["year"] = year

    if month:
        additional_filters += " AND month = :month"
        filter_params["month"] = month

    if speaker:
        additional_filters += " AND speaker_name ILIKE :speaker"
        filter_params["speaker"] = f"%{speaker}%"

    # Execute search
    results = execute_vector_search(
        session=session,
        table="conference_paragraphs",
        query_embedding=query_embedding,
        lang=lang,
        limit=limit,
        select_columns=(
            "id, year, month, session, talk_uri, talk_title, speaker_name, "
            "speaker_role, paragraph_num, text, context_text, scripture_refs, lang"
        ),
        additional_filters=additional_filters,
        filter_params=filter_params,
    )

    # Format results
    formatted_results = []
    for row in results:
        formatted_results.append({
            "id": row["id"],
            "year": row["year"],
            "month": row["month"],
            "session": row["session"],
            "talk_uri": row["talk_uri"],
            "talk_title": row["talk_title"],
            "speaker_name": row["speaker_name"],
            "speaker_role": row["speaker_role"],
            "paragraph_num": row["paragraph_num"],
            "text": row["text"],
            "context_text": row["context_text"],
            "scripture_refs": row["scripture_refs"],
            "lang": row["lang"],
            "similarity": round(row["similarity"], 4),
        })

    return formatted_results
