"""Scripture search schema definitions.

This module contains Pydantic models for scripture search requests
and responses, including volume/book filtering and reference formatting.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.api.schemas.common import Language, SearchRequest, SearchResultMeta


class ScriptureVolume(str, Enum):
    """Scripture volume identifiers.

    Values correspond to the volume column in the scriptures table.
    """

    oldtestament = "oldtestament"
    newtestament = "newtestament"
    bookofmormon = "bookofmormon"
    doctrineandcovenants = "doctrineandcovenants"
    pearlofgreatprice = "pearlofgreatprice"


class ScriptureSearchRequest(SearchRequest):
    """Request model for scripture semantic search.

    Extends the base SearchRequest with optional volume and book filters
    to narrow search results to specific scriptures.

    Attributes:
        volume: Optional filter for scripture volume
        book: Optional filter for specific book within a volume
    """

    volume: Optional[ScriptureVolume] = Field(
        default=None,
        description="Filter results to a specific scripture volume",
    )
    book: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Filter results to a specific book (e.g., 'alma', 'genesis')",
        json_schema_extra={"example": "alma"},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "faith in Jesus Christ",
                    "lang": "en",
                    "limit": 10,
                    "volume": "bookofmormon",
                },
                {
                    "query": "la fe en Jesucristo",
                    "lang": "es",
                    "limit": 5,
                    "volume": "bookofmormon",
                    "book": "alma",
                },
            ]
        }
    }


class ScriptureResult(BaseModel):
    """Individual scripture search result.

    Represents a single scripture verse returned from semantic search,
    including the verse content, location, and similarity score.

    Attributes:
        id: Database ID of the scripture verse
        volume: Scripture volume containing the verse
        book: Book name within the volume
        chapter: Chapter number
        verse: Verse number
        text: Full text of the verse
        lang: Language of the verse
        context_text: Surrounding verses for context (if available)
        similarity: Semantic similarity score (0-1, higher is more similar)
        reference: Formatted reference string (e.g., "Alma 32:21")
    """

    id: int = Field(
        ...,
        description="Database ID of the scripture verse",
    )
    volume: str = Field(
        ...,
        description="Scripture volume (e.g., 'bookofmormon')",
    )
    book: str = Field(
        ...,
        description="Book name (e.g., 'alma')",
    )
    chapter: int = Field(
        ...,
        description="Chapter number",
    )
    verse: int = Field(
        ...,
        description="Verse number",
    )
    text: str = Field(
        ...,
        description="Full text of the verse",
    )
    lang: str = Field(
        ...,
        description="Language code ('en' or 'es')",
    )
    context_text: Optional[str] = Field(
        default=None,
        description="Surrounding verses for additional context",
    )
    similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Semantic similarity score (0-1)",
    )
    reference: str = Field(
        ...,
        description="Formatted reference (e.g., 'Alma 32:21')",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 12345,
                    "volume": "bookofmormon",
                    "book": "alma",
                    "chapter": 32,
                    "verse": 21,
                    "text": "And now as I said concerning faith...",
                    "lang": "en",
                    "context_text": "Alma 32:19-23: ...",
                    "similarity": 0.8723,
                    "reference": "Alma 32:21",
                }
            ]
        }
    }


class ScriptureSearchResponse(BaseModel):
    """Response model for scripture search endpoint.

    Contains a list of search results and metadata about the search operation.

    Attributes:
        results: List of matching scripture verses
        meta: Metadata about the search (query, count, timing)
    """

    results: list[ScriptureResult] = Field(
        ...,
        description="List of matching scripture verses",
    )
    meta: SearchResultMeta = Field(
        ...,
        description="Search metadata (query, count, timing)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "results": [
                        {
                            "id": 12345,
                            "volume": "bookofmormon",
                            "book": "alma",
                            "chapter": 32,
                            "verse": 21,
                            "text": "And now as I said concerning faith...",
                            "lang": "en",
                            "context_text": "Alma 32:19-23: ...",
                            "similarity": 0.8723,
                            "reference": "Alma 32:21",
                        }
                    ],
                    "meta": {
                        "query": "faith in Jesus Christ",
                        "total_results": 1,
                        "search_time_ms": 127.5,
                    },
                }
            ]
        }
    }
