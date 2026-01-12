"""General Conference talk search schema definitions.

This module contains Pydantic models for conference talk search requests
and responses, including year/month/speaker filtering.
"""

from typing import Optional

from pydantic import BaseModel, Field

from src.api.schemas.common import SearchRequest, SearchResultMeta


class ConferenceSearchRequest(SearchRequest):
    """Request model for General Conference talk semantic search.

    Extends the base SearchRequest with optional year, month, and speaker
    filters to narrow search results to specific conference talks.

    Attributes:
        year: Optional filter for conference year (2014-2030)
        month: Optional filter for conference month ("04" or "10")
        speaker: Optional partial match filter for speaker name
    """

    year: Optional[int] = Field(
        default=None,
        ge=2014,
        le=2030,
        description="Filter results to a specific year (2014-2030)",
    )
    month: Optional[str] = Field(
        default=None,
        pattern="^(04|10)$",
        description="Filter results to a specific month ('04' for April or '10' for October)",
    )
    speaker: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Partial match filter for speaker name",
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
                    "month": "04",
                    "speaker": "Nelson",
                },
            ]
        }
    }


class ConferenceResult(BaseModel):
    """Individual conference talk search result.

    Represents a single paragraph from a General Conference talk returned
    from semantic search, including the talk metadata and similarity score.

    Attributes:
        id: Database ID of the conference paragraph
        year: Conference year
        month: Conference month ("04" or "10")
        session: Session name (saturday_morning, etc.)
        talk_uri: Full URI path to the talk
        talk_title: Talk title
        speaker_name: Speaker name
        speaker_role: Speaker calling/role
        paragraph_num: 1-indexed position in talk
        text: Paragraph text
        context_text: Surrounding context text (optional)
        scripture_refs: List of scripture references in the paragraph
        lang: Language of the talk
        similarity: Semantic similarity score (0-1, higher is more similar)
    """

    id: int = Field(
        ...,
        description="Database ID of the conference paragraph",
    )
    year: int = Field(
        ...,
        description="Conference year (e.g., 2024)",
    )
    month: str = Field(
        ...,
        description="Conference month ('04' or '10')",
    )
    session: Optional[str] = Field(
        default=None,
        description="Session name (saturday_morning, saturday_afternoon, etc.)",
    )
    talk_uri: str = Field(
        ...,
        description="Full URI path to the talk",
    )
    talk_title: Optional[str] = Field(
        default=None,
        description="Talk title",
    )
    speaker_name: Optional[str] = Field(
        default=None,
        description="Speaker name",
    )
    speaker_role: Optional[str] = Field(
        default=None,
        description="Speaker calling/role",
    )
    paragraph_num: int = Field(
        ...,
        description="1-indexed position in the talk",
    )
    text: str = Field(
        ...,
        description="Paragraph text",
    )
    context_text: Optional[str] = Field(
        default=None,
        description="Surrounding context text for the paragraph",
    )
    scripture_refs: Optional[list[str]] = Field(
        default=None,
        description="List of scripture references in the paragraph",
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
                    "id": 1234,
                    "year": 2024,
                    "month": "10",
                    "session": "saturday_morning",
                    "talk_uri": "/general-conference/2024/10/12andersen",
                    "talk_title": "The Faith to Ask and Then to Act",
                    "speaker_name": "Elder Neil L. Andersen",
                    "speaker_role": "Of the Quorum of the Twelve Apostles",
                    "paragraph_num": 5,
                    "text": "Faith in Jesus Christ is the foundation of all righteousness...",
                    "context_text": None,
                    "scripture_refs": ["Hebrews 11:1", "Alma 32:21"],
                    "lang": "en",
                    "similarity": 0.8542,
                }
            ]
        }
    }


class ConferenceSearchResponse(BaseModel):
    """Response model for conference talk search endpoint.

    Contains a list of search results and metadata about the search operation.

    Attributes:
        results: List of matching conference paragraphs
        meta: Metadata about the search (query, count, timing)
    """

    results: list[ConferenceResult] = Field(
        ...,
        description="List of matching conference paragraphs",
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
                            "id": 1234,
                            "year": 2024,
                            "month": "10",
                            "session": "saturday_morning",
                            "talk_uri": "/general-conference/2024/10/12andersen",
                            "talk_title": "The Faith to Ask and Then to Act",
                            "speaker_name": "Elder Neil L. Andersen",
                            "speaker_role": "Of the Quorum of the Twelve Apostles",
                            "paragraph_num": 5,
                            "text": "Faith in Jesus Christ is the foundation of all righteousness...",
                            "context_text": None,
                            "scripture_refs": ["Hebrews 11:1", "Alma 32:21"],
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
