"""Common schema definitions for Scripture Search API.

This module contains shared schema components used across all search endpoints:
- Language enum for supported languages
- SearchRequest base model for all search requests
- SearchResultMeta for response metadata
"""

from enum import Enum

from pydantic import BaseModel, Field


class Language(str, Enum):
    """Supported languages for scripture search.

    Values:
        en: English
        es: Spanish (Espanol)
    """

    en = "en"
    es = "es"


class SearchRequest(BaseModel):
    """Base model for all search requests.

    This model provides common fields for semantic search across
    scriptures, Come Follow Me lessons, and conference talks.

    Attributes:
        query: Natural language search query
        lang: Language to search in (English or Spanish)
        limit: Maximum number of results to return
    """

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Natural language search query (3-500 characters)",
        json_schema_extra={"example": "faith in Jesus Christ"},
    )
    lang: Language = Field(
        default=Language.en,
        description="Language to search in",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return (1-50)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "faith in Jesus Christ",
                    "lang": "en",
                    "limit": 10,
                }
            ]
        }
    }


class SearchResultMeta(BaseModel):
    """Metadata about search results.

    Included in all search responses to provide context about
    the search operation and results.

    Attributes:
        query: The original search query
        total_results: Number of results returned
        search_time_ms: Time taken to perform the search in milliseconds
    """

    query: str = Field(
        ...,
        description="The original search query",
    )
    total_results: int = Field(
        ...,
        ge=0,
        description="Number of results returned",
    )
    search_time_ms: float = Field(
        ...,
        ge=0,
        description="Search execution time in milliseconds",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "faith in Jesus Christ",
                    "total_results": 10,
                    "search_time_ms": 127.5,
                }
            ]
        }
    }
