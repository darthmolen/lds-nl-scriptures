"""Come Follow Me (CFM) lesson search router.

This module provides the FastAPI router for CFM lesson semantic search,
exposing the POST /api/v1/cfm/search endpoint.
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas.cfm import (
    CFMResult,
    CFMSearchRequest,
    CFMSearchResponse,
)
from src.api.schemas.common import SearchResultMeta
from src.api.services.cfm import search_cfm_lessons
from src.embeddings.client import get_single_embedding

router = APIRouter(
    prefix="/cfm",
    tags=["cfm"],
)


@router.post(
    "/search",
    response_model=CFMSearchResponse,
    summary="Search Come Follow Me lessons semantically",
    description="""
    Perform semantic search across Come Follow Me (CFM) lessons using natural language queries.

    Returns lessons ranked by semantic similarity to the query, with optional
    filtering by year (2019-2030) and testament (ot, nt, bom, dc).

    The search uses vector embeddings and cosine similarity for ranking.
    """,
)
def cfm_search(
    request: CFMSearchRequest,
    db: Session = Depends(get_db),
) -> CFMSearchResponse:
    """Search CFM lessons by semantic similarity.

    Args:
        request: Search request with query, filters, and options
        db: Database session (injected)

    Returns:
        CFMSearchResponse with results and metadata

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
        results = search_cfm_lessons(
            session=db,
            query_embedding=query_embedding,
            lang=request.lang.value,
            limit=request.limit,
            year=request.year,
            testament=request.testament.value if request.testament else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )

    # Calculate elapsed time
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Build response
    return CFMSearchResponse(
        results=[CFMResult(**r) for r in results],
        meta=SearchResultMeta(
            query=request.query,
            total_results=len(results),
            search_time_ms=round(elapsed_ms, 2),
        ),
    )
