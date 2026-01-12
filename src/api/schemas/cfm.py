"""Come Follow Me (CFM) search schema definitions.

This module contains Pydantic models for CFM lesson search requests
and responses, including year/testament filtering.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.api.schemas.common import Language, SearchRequest, SearchResultMeta


class CFMTestament(str, Enum):
    """CFM testament/scripture focus identifiers.

    Values correspond to the testament column in the cfm_lessons table.
    """

    ot = "ot"
    nt = "nt"
    bom = "bom"
    dc = "dc"


class CFMSearchRequest(SearchRequest):
    """Request model for CFM lesson semantic search.

    Extends the base SearchRequest with optional year and testament filters
    to narrow search results to specific CFM lessons.

    Attributes:
        year: Optional filter for lesson year (2019-2030)
        testament: Optional filter for scripture focus (ot, nt, bom, dc)
    """

    year: Optional[int] = Field(
        default=None,
        ge=2019,
        le=2030,
        description="Filter results to a specific year (2019-2030)",
    )
    testament: Optional[CFMTestament] = Field(
        default=None,
        description="Filter results to a specific testament/scripture focus",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "How can I strengthen my faith?",
                    "lang": "en",
                    "limit": 10,
                    "year": 2024,
                },
                {
                    "query": "El arrepentimiento y el perdon",
                    "lang": "es",
                    "limit": 5,
                    "testament": "bom",
                },
            ]
        }
    }


class CFMResult(BaseModel):
    """Individual CFM lesson search result.

    Represents a single CFM lesson returned from semantic search,
    including the lesson content preview and similarity score.

    Attributes:
        id: Database ID of the CFM lesson
        year: Lesson year
        testament: Scripture focus (ot, nt, bom, dc)
        lesson_id: Unique lesson identifier
        title: Lesson title
        date_range: Date range string for the lesson
        scripture_refs: List of scripture references
        content_preview: First 500 characters of lesson content
        lang: Language of the lesson
        similarity: Semantic similarity score (0-1, higher is more similar)
    """

    id: int = Field(
        ...,
        description="Database ID of the CFM lesson",
    )
    year: int = Field(
        ...,
        description="Lesson year (e.g., 2024)",
    )
    testament: Optional[str] = Field(
        default=None,
        description="Scripture focus (ot, nt, bom, dc)",
    )
    lesson_id: str = Field(
        ...,
        description="Unique lesson identifier",
    )
    title: Optional[str] = Field(
        default=None,
        description="Lesson title",
    )
    date_range: Optional[str] = Field(
        default=None,
        description="Date range for the lesson",
    )
    scripture_refs: Optional[list[str]] = Field(
        default=None,
        description="List of scripture references covered in the lesson",
    )
    content_preview: str = Field(
        ...,
        description="First 500 characters of lesson content",
    )
    lang: str = Field(
        ...,
        description="Language code ('en' or 'es')",
    )
    similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Semantic similarity score (0-1)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 42,
                    "year": 2024,
                    "testament": "bom",
                    "lesson_id": "15-faith",
                    "title": "What Is Faith?",
                    "date_range": "April 8-14",
                    "scripture_refs": ["Alma 32:21", "Hebrews 11:1"],
                    "content_preview": "Faith is not to have a perfect knowledge...",
                    "lang": "en",
                    "similarity": 0.8542,
                }
            ]
        }
    }


class CFMSearchResponse(BaseModel):
    """Response model for CFM lesson search endpoint.

    Contains a list of search results and metadata about the search operation.

    Attributes:
        results: List of matching CFM lessons
        meta: Metadata about the search (query, count, timing)
    """

    results: list[CFMResult] = Field(
        ...,
        description="List of matching CFM lessons",
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
                            "id": 42,
                            "year": 2024,
                            "testament": "bom",
                            "lesson_id": "15-faith",
                            "title": "What Is Faith?",
                            "date_range": "April 8-14",
                            "scripture_refs": ["Alma 32:21", "Hebrews 11:1"],
                            "content_preview": "Faith is not to have a perfect knowledge...",
                            "lang": "en",
                            "similarity": 0.8542,
                        }
                    ],
                    "meta": {
                        "query": "How can I strengthen my faith?",
                        "total_results": 1,
                        "search_time_ms": 142.3,
                    },
                }
            ]
        }
    }
