"""Conference talk ingestion module.

Provides utilities for fetching and processing General Conference talks
from the Church content API.

Submodules:
- client: Church API client for fetching conference manifests and talks
- parser: HTML parser for conference talk content
- ingest: Database ingestion script

Exports:
- ChurchAPIClient: HTTP client for Church content API
- TalkMetadata: Dataclass for talk metadata
- ConferenceManifest: Dataclass for conference manifest
- get_all_conferences: Helper to list all conference (year, month) tuples
- parse_talk: Parse API response into structured talk data
- get_content_paragraphs: Get only content paragraphs (exclude metadata)
- ParsedTalk: Fully parsed conference talk dataclass
- Paragraph: A parsed paragraph from a talk
- Footnote: A footnote reference
- ingest_conference: Ingest a single conference into database
"""

from src.ingestion.conference.client import (
    ChurchAPIClient,
    ConferenceManifest,
    TalkMetadata,
    get_all_conferences,
)
from src.ingestion.conference.parser import (
    Footnote,
    Paragraph,
    ParsedTalk,
    get_content_paragraphs,
    get_footnotes_for_paragraph,
    get_paragraph_by_id,
    parse_talk,
)
from src.ingestion.conference.ingest import ingest_conference

__all__ = [
    # Client exports
    "ChurchAPIClient",
    "ConferenceManifest",
    "TalkMetadata",
    "get_all_conferences",
    # Parser exports
    "parse_talk",
    "get_content_paragraphs",
    "get_paragraph_by_id",
    "get_footnotes_for_paragraph",
    "ParsedTalk",
    "Paragraph",
    "Footnote",
    # Ingest exports
    "ingest_conference",
]
