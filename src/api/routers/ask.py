"""Ask (RAG generation) router.

This module provides the FastAPI router for RAG-based question answering,
exposing the POST /api/v1/ask endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.api.schemas.generation import (
    AskRequest,
    AskResponse,
    AskResponseMeta,
    Citation,
)
from src.api.services.generation import get_generation_service

router = APIRouter(
    prefix="/ask",
    tags=["ask"],
)


@router.post(
    "",
    response_model=AskResponse,
    summary="Ask a question using RAG",
    description="""
    Answer a question using Retrieval-Augmented Generation (RAG) with scripture context.

    The endpoint:
    1. Searches for relevant scripture verses using semantic search
    2. Uses the verses as context for an LLM to generate an answer
    3. Returns the answer with scripture citations

    Optionally filter the scripture search by volume (e.g., Book of Mormon)
    or book (e.g., Alma) using the filters parameter.

    The response includes metadata about search and generation timing,
    as well as the specific scriptures cited in the answer.
    """,
    responses={
        200: {
            "description": "Successfully generated answer",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "The Book of Mormon teaches that faith is a principle of action...",
                        "citations": [
                            {
                                "reference": "Alma 32:21",
                                "text": "And now as I said concerning faith...",
                            }
                        ],
                        "meta": {
                            "model": "gpt-4o-mini",
                            "search_time_ms": 127.5,
                            "generation_time_ms": 1523.8,
                            "context_verses": 10,
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service unavailable (embedding or generation failed)",
        },
        500: {
            "description": "Internal server error",
        },
    },
)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
) -> AskResponse:
    """Answer a question using RAG with scripture context.

    Args:
        request: Ask request with question, optional filters, and options
        db: Database session (injected)

    Returns:
        AskResponse with answer, citations, and metadata

    Raises:
        HTTPException: If embedding or generation service fails
    """
    service = get_generation_service()

    try:
        result = service.ask(
            session=db,
            question=request.question,
            lang=request.lang.value,
            top_k=request.top_k,
            filters=request.filters,
        )
    except Exception as e:
        error_msg = str(e)
        if "embedding" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Embedding service unavailable: {error_msg}",
            )
        elif "openai" in error_msg.lower() or "completion" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail=f"Generation service unavailable: {error_msg}",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ask failed: {error_msg}",
            )

    # Build response
    return AskResponse(
        answer=result["answer"],
        citations=[Citation(**c) for c in result["citations"]],
        meta=AskResponseMeta(**result["meta"]),
    )
