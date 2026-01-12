"""Scripture search service.

This module provides scripture-specific search functionality,
building on the core vector search with scripture filters and
reference formatting.
"""

from typing import Optional

from sqlalchemy.orm import Session

from src.api.services.search import execute_vector_search
from src.embeddings.context import format_book_title


def search_scriptures(
    session: Session,
    query_embedding: list[float],
    lang: str,
    limit: int,
    volume: Optional[str] = None,
    book: Optional[str] = None,
) -> list[dict]:
    """Search scriptures by semantic similarity.

    Performs a vector similarity search against the scriptures table,
    optionally filtered by volume and/or book.

    Args:
        session: SQLAlchemy database session
        query_embedding: Query vector (1536 dimensions)
        lang: Language code ('en' or 'es')
        limit: Maximum number of results
        volume: Optional volume filter (e.g., 'bookofmormon')
        book: Optional book filter (e.g., 'alma')

    Returns:
        List of scripture result dictionaries with formatted references
    """
    # Build optional filters
    additional_filters = ""
    filter_params = {}

    if volume:
        additional_filters += " AND volume = :volume"
        filter_params["volume"] = volume

    if book:
        additional_filters += " AND book = :book"
        filter_params["book"] = book

    # Execute search
    results = execute_vector_search(
        session=session,
        table="scriptures",
        query_embedding=query_embedding,
        lang=lang,
        limit=limit,
        select_columns="id, volume, book, chapter, verse, text, lang, context_text",
        additional_filters=additional_filters,
        filter_params=filter_params,
    )

    # Format results with reference strings
    formatted_results = []
    for row in results:
        book_title = format_book_title(row["book"])
        reference = f"{book_title} {row['chapter']}:{row['verse']}"

        formatted_results.append({
            "id": row["id"],
            "volume": row["volume"],
            "book": row["book"],
            "chapter": row["chapter"],
            "verse": row["verse"],
            "text": row["text"],
            "lang": row["lang"],
            "context_text": row["context_text"],
            "similarity": round(row["similarity"], 4),
            "reference": reference,
        })

    return formatted_results
