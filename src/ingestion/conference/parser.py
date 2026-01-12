"""HTML parser for General Conference talks.

Handles all HTML format variations across conference history:
- 2014-2024/04: Sequential IDs (p1, p2, author1, kicker1, subtitle1)
- 2024/10+: Hash IDs (p_ks9eS, p_qFFZG)

The parser uses DOM order for paragraph numbering to work consistently
regardless of ID format. This approach is resilient to future format changes.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class Paragraph:
    """A parsed paragraph from a talk.

    Attributes:
        paragraph_num: 1-indexed position in DOM order
        text: Plain text content (HTML stripped)
        html: Original HTML markup
        paragraph_id: Original ID attribute from the HTML
        is_metadata: True for author/kicker paragraphs (non-content)
    """

    paragraph_num: int
    text: str
    html: str
    paragraph_id: str
    is_metadata: bool = False


@dataclass
class Footnote:
    """A footnote reference from a talk.

    Attributes:
        note_id: Unique identifier (e.g., "note1")
        marker: Display marker (e.g., "1", "2")
        paragraph_id: ID of the paragraph containing this footnote
        text: Full footnote text
        reference_uris: List of scripture/talk URIs referenced
    """

    note_id: str
    marker: str
    paragraph_id: str
    text: str
    reference_uris: list[str] = field(default_factory=list)


@dataclass
class ParsedTalk:
    """Fully parsed conference talk.

    Attributes:
        title: Talk title
        speaker_name: Speaker's name (without "By " prefix)
        speaker_role: Speaker's calling/role
        paragraphs: All paragraphs in DOM order
        footnotes: All footnote references
        scripture_refs: Extracted scripture references (deduplicated)
        talk_refs: Cross-references to other conference talks
    """

    title: str
    speaker_name: str
    speaker_role: str
    paragraphs: list[Paragraph]
    footnotes: list[Footnote]
    scripture_refs: list[str]
    talk_refs: list[str]


def parse_talk(api_response: dict) -> ParsedTalk:
    """Parse API response into structured talk data.

    Works with all HTML format variations by using DOM order
    for paragraph numbering rather than relying on ID formats.

    Args:
        api_response: Raw API response from ChurchAPIClient.fetch_talk()

    Returns:
        ParsedTalk with all extracted data

    Example:
        >>> response = client.fetch_talk(2024, 10, "12andersen", "en")
        >>> talk = parse_talk(response)
        >>> print(talk.speaker_name)
        'Elder Neil L. Andersen'
    """
    content = api_response.get("content", {})
    body_html = content.get("body", "")
    footnotes_data = content.get("footnotes", {})

    soup = BeautifulSoup(body_html, "html.parser")

    # Extract title
    title = _extract_title(soup) or content.get("title", "")

    # Extract speaker
    speaker_name, speaker_role = _extract_speaker(soup)

    # Extract all paragraphs by DOM order
    paragraphs = _extract_paragraphs(soup)

    # Parse footnotes
    footnotes = _parse_footnotes(footnotes_data)

    # Extract scripture references
    scripture_refs = _extract_scripture_refs(soup)

    # Extract talk cross-references
    talk_refs = _extract_talk_refs(footnotes)

    return ParsedTalk(
        title=title,
        speaker_name=speaker_name,
        speaker_role=speaker_role,
        paragraphs=paragraphs,
        footnotes=footnotes,
        scripture_refs=scripture_refs,
        talk_refs=talk_refs,
    )


def _extract_title(soup: BeautifulSoup) -> str:
    """Extract talk title from HTML.

    Tries multiple strategies:
    1. First <h1> element
    2. Element with class="title"

    Args:
        soup: Parsed HTML document

    Returns:
        Extracted title or empty string if not found
    """
    # Try h1 first
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    # Try title class
    title_el = soup.find(class_="title")
    if title_el:
        return title_el.get_text(strip=True)

    return ""


def _extract_speaker(soup: BeautifulSoup) -> tuple[str, str]:
    """Extract speaker name and role from HTML.

    Looks for elements with class="author-name" and class="author-role".
    Cleans up common prefixes like "By " from the speaker name.

    Args:
        soup: Parsed HTML document

    Returns:
        (speaker_name, speaker_role) tuple, either may be empty string
    """
    name = ""
    role = ""

    # Find author-name class
    author_name = soup.find(class_="author-name")
    if author_name:
        name = author_name.get_text(strip=True)
        # Clean up "By " prefix (case-insensitive)
        if name.lower().startswith("by "):
            name = name[3:]
        # Clean up "Presented by " prefix (for statistical reports)
        if name.lower().startswith("presented by "):
            name = name[13:]

    # Find author-role class
    author_role = soup.find(class_="author-role")
    if author_role:
        role = author_role.get_text(strip=True)

    return name, role


def _extract_paragraphs(soup: BeautifulSoup) -> list[Paragraph]:
    """Extract paragraphs by DOM order.

    Uses DOM order for numbering to handle both sequential and hash ID formats.
    Identifies metadata paragraphs (author, kicker) vs content paragraphs.

    Args:
        soup: Parsed HTML document

    Returns:
        List of Paragraph objects in DOM order
    """
    paragraphs = []
    para_num = 0

    # Find all <p> tags with id attribute
    for p in soup.find_all("p", id=True):
        p_id = p.get("id", "")
        p_classes = p.get("class", [])
        if isinstance(p_classes, str):
            p_classes = [p_classes]
        p_class = " ".join(p_classes)

        # Skip empty paragraphs
        text = p.get_text(strip=True)
        if not text:
            continue

        # Skip subtitle paragraphs (usually redundant with title)
        if p_id.startswith("subtitle"):
            continue

        # Determine if this is metadata (author, kicker) vs content
        metadata_classes = {"author-name", "author-role", "kicker"}
        is_metadata = bool(metadata_classes & set(p_classes))

        # Also detect by ID pattern for older formats
        if not is_metadata and (
            p_id.startswith("author") or p_id.startswith("kicker")
        ):
            is_metadata = True

        para_num += 1
        paragraphs.append(
            Paragraph(
                paragraph_num=para_num,
                text=text,
                html=str(p),
                paragraph_id=p_id,
                is_metadata=is_metadata,
            )
        )

    return paragraphs


def _parse_footnotes(footnotes_data: dict) -> list[Footnote]:
    """Parse footnotes from API response.

    Footnotes format from API:
    {
        "note1": {"id": "note1", "marker": "1", "pid": "p3", "text": "...", "referenceUris": [...]},
        ...
    }

    Args:
        footnotes_data: Footnotes dictionary from API response

    Returns:
        List of Footnote objects
    """
    footnotes = []

    if not footnotes_data:
        return footnotes

    for note_key, note in footnotes_data.items():
        if not isinstance(note, dict):
            continue

        footnotes.append(
            Footnote(
                note_id=note.get("id", note_key),
                marker=str(note.get("marker", "")),
                paragraph_id=note.get("pid", ""),
                text=note.get("text", ""),
                reference_uris=note.get("referenceUris", []) or [],
            )
        )

    return footnotes


def _extract_scripture_refs(soup: BeautifulSoup) -> list[str]:
    """Extract scripture references from HTML.

    Looks for <a class="scripture-ref"> elements which contain
    clickable scripture citations.

    Args:
        soup: Parsed HTML document

    Returns:
        Deduplicated list of scripture references preserving order
    """
    refs = []

    for a in soup.find_all("a", class_="scripture-ref"):
        ref_text = a.get_text(strip=True)
        if ref_text:
            refs.append(ref_text)

    # Dedupe while preserving order
    return list(dict.fromkeys(refs))


def _extract_talk_refs(footnotes: list[Footnote]) -> list[str]:
    """Extract cross-references to other conference talks from footnotes.

    Looks for URIs containing "/general-conference/" in footnote references.

    Args:
        footnotes: List of parsed footnotes

    Returns:
        Deduplicated list of talk URIs preserving order
    """
    refs = []

    for fn in footnotes:
        for uri in fn.reference_uris:
            if "/general-conference/" in uri:
                refs.append(uri)

    # Dedupe while preserving order
    return list(dict.fromkeys(refs))


def get_content_paragraphs(talk: ParsedTalk) -> list[Paragraph]:
    """Get only content paragraphs (exclude metadata like author/kicker).

    Filters out paragraphs marked as metadata, returning only the
    actual talk content suitable for embedding.

    Args:
        talk: Parsed talk object

    Returns:
        List of content paragraphs only

    Example:
        >>> content = get_content_paragraphs(talk)
        >>> for p in content:
        ...     print(f"{p.paragraph_num}: {p.text[:50]}...")
    """
    return [p for p in talk.paragraphs if not p.is_metadata]


def get_paragraph_by_id(talk: ParsedTalk, paragraph_id: str) -> Optional[Paragraph]:
    """Get a specific paragraph by its original ID.

    Args:
        talk: Parsed talk object
        paragraph_id: Original paragraph ID (e.g., "p3" or "p_ks9eS")

    Returns:
        Matching Paragraph or None if not found
    """
    for p in talk.paragraphs:
        if p.paragraph_id == paragraph_id:
            return p
    return None


def get_footnotes_for_paragraph(
    talk: ParsedTalk, paragraph_id: str
) -> list[Footnote]:
    """Get all footnotes for a specific paragraph.

    Args:
        talk: Parsed talk object
        paragraph_id: Original paragraph ID

    Returns:
        List of Footnote objects linked to this paragraph
    """
    return [fn for fn in talk.footnotes if fn.paragraph_id == paragraph_id]
