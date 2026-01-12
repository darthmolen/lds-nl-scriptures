"""Church API client for General Conference talks.

Provides a production-ready client for fetching conference manifests and
individual talk content from the Church content API.

Usage:
    from src.ingestion.conference.client import ChurchAPIClient, get_all_conferences

    client = ChurchAPIClient(lang="eng")

    # Fetch manifest for a specific conference
    manifest = client.fetch_conference_manifest(2024, "10")
    print(f"Found {len(manifest.talks)} talks")

    # Fetch individual talk content
    for talk in manifest.talks:
        content = client.fetch_talk(talk.uri)
        html = content.get("content", {}).get("body", "")
        # Process HTML...

    # Get all conferences in date range
    for year, month in get_all_conferences(2020, 2024):
        manifest = client.fetch_conference_manifest(year, month)
        # Process...
"""

import re
import time
from dataclasses import dataclass

import requests

BASE_URL = "https://www.churchofjesuschrist.org"
API_PATH = "/study/api/v3/language-pages/type/content"


@dataclass
class TalkMetadata:
    """Metadata for a conference talk.

    Attributes:
        year: Conference year (e.g., 2024)
        month: Conference month ("04" for April, "10" for October)
        talk_id: Talk identifier (e.g., "12andersen", "11oaks")
        uri: Full URI path (e.g., "/general-conference/2024/10/12andersen")
    """

    year: int
    month: str  # "04" or "10"
    talk_id: str
    uri: str  # Full URI path


@dataclass
class ConferenceManifest:
    """Manifest of talks for a conference.

    Attributes:
        year: Conference year
        month: Conference month ("04" or "10")
        talks: List of TalkMetadata for all talks in the conference
    """

    year: int
    month: str
    talks: list[TalkMetadata]


class ChurchAPIClient:
    """Client for Church content API.

    Provides rate-limited access to the Church's content API for fetching
    General Conference manifests and individual talk content.

    Attributes:
        lang: Language code for content ("eng" for English, "spa" for Spanish)
        delay: Delay between requests in seconds (default 0.5)

    Example:
        client = ChurchAPIClient(lang="eng", delay=0.5)
        manifest = client.fetch_conference_manifest(2024, "10")
        for talk in manifest.talks:
            content = client.fetch_talk(talk.uri)
    """

    def __init__(self, lang: str = "eng", delay: float = 0.5):
        """Initialize the Church API client.

        Args:
            lang: Language code ("eng" for English, "spa" for Spanish)
            delay: Delay between requests in seconds (default 0.5)
        """
        self.lang = lang
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Scripture-Search/1.0 (Educational)",
                "Accept": "application/json",
            }
        )
        self._last_request: float = 0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.time()

    def fetch_conference_manifest(self, year: int, month: str) -> ConferenceManifest:
        """Fetch list of talks for a conference.

        Args:
            year: Conference year (2014-2025)
            month: "04" for April, "10" for October

        Returns:
            ConferenceManifest with list of talk metadata

        Raises:
            requests.HTTPError: If the API request fails
            requests.Timeout: If the request times out
        """
        self._rate_limit()

        uri = f"/general-conference/{year}/{month}"
        url = f"{BASE_URL}{API_PATH}?lang={self.lang}&uri={uri}"

        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        body_html = data.get("content", {}).get("body", "")

        # Extract talk URIs from manifest HTML
        talk_pattern = rf"/study/general-conference/{year}/{month}/([^\"?]+)"
        matches = re.findall(talk_pattern, body_html)

        # Dedupe while preserving order
        seen: set[str] = set()
        talks: list[TalkMetadata] = []
        for talk_id in matches:
            if talk_id not in seen and not talk_id.startswith("_"):
                seen.add(talk_id)
                talks.append(
                    TalkMetadata(
                        year=year,
                        month=month,
                        talk_id=talk_id,
                        uri=f"/general-conference/{year}/{month}/{talk_id}",
                    )
                )

        return ConferenceManifest(year=year, month=month, talks=talks)

    def fetch_talk(self, uri: str) -> dict:
        """Fetch raw talk content.

        Args:
            uri: Talk URI (e.g., "/general-conference/2024/10/12andersen")

        Returns:
            Raw API response dict with content.body HTML

        Raises:
            requests.HTTPError: If the API request fails
            requests.Timeout: If the request times out
        """
        self._rate_limit()

        url = f"{BASE_URL}{API_PATH}?lang={self.lang}&uri={uri}"

        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()

        return resp.json()


def get_all_conferences(
    start_year: int = 2014, end_year: int = 2025
) -> list[tuple[int, str]]:
    """Get list of all conference (year, month) tuples.

    Generates a chronological list of all General Conference sessions
    between the specified years. April conferences use month "04" and
    October conferences use month "10".

    Args:
        start_year: Starting year (inclusive, default 2014)
        end_year: Ending year (inclusive, default 2025)

    Returns:
        List of (year, month) tuples in chronological order

    Example:
        >>> get_all_conferences(2023, 2024)
        [(2023, '04'), (2023, '10'), (2024, '04'), (2024, '10')]
    """
    conferences: list[tuple[int, str]] = []
    for year in range(start_year, end_year + 1):
        for month in ["04", "10"]:
            # Skip future conferences
            if year == 2025 and month == "10":
                continue
            conferences.append((year, month))
    return conferences
