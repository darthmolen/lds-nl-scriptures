"""Scripture search router.

This module provides the FastAPI router for scripture semantic search,
exposing the POST /api/v1/scriptures/search endpoint.
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas.common import SearchResultMeta
from src.api.schemas.scriptures import (
    ScriptureResult,
    ScriptureSearchRequest,
    ScriptureSearchResponse,
)
from src.api.services.scriptures import search_scriptures
from src.embeddings.client import get_single_embedding

router = APIRouter(
    prefix="/scriptures",
    tags=["scriptures"],
)


@router.post(
    "/search",
    response_model=ScriptureSearchResponse,
    summary="Search scriptures semantically",
    description="""
    Perform semantic search across scripture verses using natural language queries.

    Returns verses ranked by semantic similarity to the query, with optional
    filtering by volume (e.g., Book of Mormon) and book (e.g., Alma).

    The search uses vector embeddings and cosine similarity for ranking.
    """,
)
def scripture_search(
    request: ScriptureSearchRequest,
    db: Session = Depends(get_db),
) -> ScriptureSearchResponse:
    """Search scriptures by semantic similarity.

    Args:
        request: Search request with query, filters, and options
        db: Database session (injected)

    Returns:
        ScriptureSearchResponse with results and metadata

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
        results = search_scriptures(
            session=db,
            query_embedding=query_embedding,
            lang=request.lang.value,
            limit=request.limit,
            volume=request.volume.value if request.volume else None,
            book=request.book,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )

    # Calculate elapsed time
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Build response
    return ScriptureSearchResponse(
        results=[ScriptureResult(**r) for r in results],
        meta=SearchResultMeta(
            query=request.query,
            total_results=len(results),
            search_time_ms=round(elapsed_ms, 2),
        ),
    )
