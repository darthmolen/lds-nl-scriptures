"""Generation (RAG) schema definitions.

This module contains Pydantic models for the RAG-based question answering
endpoint that combines scripture search with LLM generation.
"""

from typing import Optional

from pydantic import BaseModel, Field

from src.api.schemas.common import Language


class AskRequest(BaseModel):
    """Request model for RAG-based question answering.

    Accepts a natural language question and optional filters to search
    for relevant scriptures before generating an answer.

    Attributes:
        question: The question to answer using scripture context
        filters: Optional filters for scripture search (volume, book)
        top_k: Number of scripture results to use as context
        lang: Language for search and response
    """

    question: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Natural language question to answer (5-1000 characters)",
        json_schema_extra={"example": "What does the Book of Mormon teach about faith?"},
    )
    filters: Optional[dict] = Field(
        default=None,
        description="Optional filters for scripture search (e.g., {'volume': 'bookofmormon', 'book': 'alma'})",
        json_schema_extra={"example": {"volume": "bookofmormon"}},
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=25,
        description="Number of scripture results to use as context (1-25)",
    )
    lang: Language = Field(
        default=Language.en,
        description="Language for search and response",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What does the Book of Mormon teach about faith?",
                    "filters": {"volume": "bookofmormon"},
                    "top_k": 10,
                    "lang": "en",
                },
                {
                    "question": "How can I find peace during trials?",
                    "top_k": 15,
                    "lang": "en",
                },
            ]
        }
    }


class Citation(BaseModel):
    """A scripture citation included in the generated answer.

    Represents a specific scripture reference used to support
    the generated answer.

    Attributes:
        reference: Formatted scripture reference (e.g., "Alma 32:21")
        text: The text of the cited scripture verse
    """

    reference: str = Field(
        ...,
        description="Formatted scripture reference (e.g., 'Alma 32:21')",
        json_schema_extra={"example": "Alma 32:21"},
    )
    text: str = Field(
        ...,
        description="Text of the cited scripture verse",
        json_schema_extra={
            "example": "And now as I said concerning faith—faith is not to have a perfect knowledge of things..."
        },
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reference": "Alma 32:21",
                    "text": "And now as I said concerning faith—faith is not to have a perfect knowledge of things; therefore if ye have faith ye hope for things which are not seen, which are true.",
                }
            ]
        }
    }


class AskResponseMeta(BaseModel):
    """Metadata about the RAG generation response.

    Provides timing and model information for debugging and monitoring.

    Attributes:
        model: The LLM model used for generation
        search_time_ms: Time spent searching for relevant scriptures
        generation_time_ms: Time spent generating the answer
        context_verses: Number of verses used as context
    """

    model: str = Field(
        ...,
        description="LLM model used for generation",
        json_schema_extra={"example": "gpt-4o-mini"},
    )
    search_time_ms: float = Field(
        ...,
        ge=0,
        description="Time spent searching for scriptures in milliseconds",
    )
    generation_time_ms: float = Field(
        ...,
        ge=0,
        description="Time spent generating the answer in milliseconds",
    )
    context_verses: int = Field(
        ...,
        ge=0,
        description="Number of scripture verses used as context",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "model": "gpt-4o-mini",
                    "search_time_ms": 127.5,
                    "generation_time_ms": 1523.8,
                    "context_verses": 10,
                }
            ]
        }
    }


class AskResponse(BaseModel):
    """Response model for RAG-based question answering.

    Contains the generated answer, supporting scripture citations,
    and metadata about the generation process.

    Attributes:
        answer: The generated answer to the question
        citations: List of scripture citations supporting the answer
        meta: Metadata about the generation (model, timing)
    """

    answer: str = Field(
        ...,
        description="Generated answer to the question",
    )
    citations: list[Citation] = Field(
        ...,
        description="Scripture citations supporting the answer",
    )
    meta: AskResponseMeta = Field(
        ...,
        description="Generation metadata (model, timing, context size)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answer": "The Book of Mormon teaches that faith is a principle of action and power...",
                    "citations": [
                        {
                            "reference": "Alma 32:21",
                            "text": "And now as I said concerning faith—faith is not to have a perfect knowledge of things...",
                        },
                        {
                            "reference": "Ether 12:6",
                            "text": "And now, I, Moroni, would speak somewhat concerning these things...",
                        },
                    ],
                    "meta": {
                        "model": "gpt-4o-mini",
                        "search_time_ms": 127.5,
                        "generation_time_ms": 1523.8,
                        "context_verses": 10,
                    },
                }
            ]
        }
    }
