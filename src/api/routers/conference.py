"""General Conference talk search router.

This module provides the FastAPI router for conference talk semantic search,
exposing the POST /api/v1/conference/search endpoint.
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas.conference import (
    ConferenceResult,
    ConferenceSearchRequest,
    ConferenceSearchResponse,
)
from src.api.schemas.common import SearchResultMeta
from src.api.services.conference import search_conference_talks
from src.embeddings.client import get_single_embedding

router = APIRouter(
    prefix="/conference",
    tags=["conference"],
)


@router.post(
    "/search",
    response_model=ConferenceSearchResponse,
    summary="Search General Conference talks semantically",
    description="""
    Perform semantic search across General Conference talks using natural language queries.

    Returns paragraphs from talks ranked by semantic similarity to the query, with optional
    filtering by year (2014-2030), month ('04' for April or '10' for October), and speaker name.

    The speaker filter performs a partial match (case-insensitive) on the speaker name.

    The search uses vector embeddings and cosine similarity for ranking.
    """,
)
def conference_search(
    request: ConferenceSearchRequest,
    db: Session = Depends(get_db),
) -> ConferenceSearchResponse:
    """Search conference talks by semantic similarity.

    Args:
        request: Search request with query, filters, and options
        db: Database session (injected)

    Returns:
        ConferenceSearchResponse with results and metadata

    Raises:
        HTTPException: If embedding generation fails
    """
    start_time = time.perf_counter()

    # Get embedding for the query
    try:
        query_embedding = get_single_embedding(request.query)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Embedding service unavailable: {str(e)}",
        )

    # Perform search
    try:
        results = search_conference_talks(
            session=db,
            query_embedding=query_embedding,
            lang=request.lang.value,
            limit=request.limit,
            year=request.year,
            month=request.month,
            speaker=request.speaker,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )

    # Calculate elapsed time
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Build response
    return ConferenceSearchResponse(
        results=[ConferenceResult(**r) for r in results],
        meta=SearchResultMeta(
            query=request.query,
            total_results=len(results),
            search_time_ms=round(elapsed_ms, 2),
        ),
    )
