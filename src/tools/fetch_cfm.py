#!/usr/bin/env python3
"""Fetch Come Follow Me content from Church API.

This script fetches Come Follow Me lessons for home and church from:
https://www.churchofjesuschrist.org/study/manual/come-follow-me-for-home-and-church-*

Supports English (eng) and Spanish (spa).

Output is saved to JSON files for later import into PostgreSQL.
"""

import json
import time
import requests
import re
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "content" / "processed" / "cfm"

# API endpoint
CHURCH_API = "https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content"

# Rate limiting
RATE_LIMIT_DELAY = 0.15  # seconds between requests

# Language mapping (ISO -> Church)
LANG_MAP = {
    "en": "eng",
    "es": "spa",
}

# Available CFM manuals (year -> (scripture slug, format type, short code))
# format: "home-and-church" (2024+) or "individuals-and-families" (2023 and earlier)
CFM_MANUALS = {
    2026: ("old-testament", "home-and-church", "ot"),
    2025: ("doctrine-and-covenants", "home-and-church", "dc"),
    2024: ("book-of-mormon", "home-and-church", "bom"),
    2023: ("new-testament", "individuals-and-families", "nt"),
    # Pattern repeats every 4 years
}


def get_lesson_uris(manual_uri: str, lang: str) -> list[dict]:
    """Get list of lesson URIs from the manual's table of contents."""
    church_lang = LANG_MAP.get(lang, lang)
    params = {"lang": church_lang, "uri": manual_uri}
    resp = requests.get(CHURCH_API, params=params, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    body = data.get("content", {}).get("body", "")

    # Parse HTML to extract lesson links
    soup = BeautifulSoup(body, "html.parser")
    lessons = []

    for link in soup.select("a.list-tile"):
        href = link.get("href", "")
        # Extract URI (strip /study prefix and lang param)
        match = re.search(r"/study(/manual/[^?\"]+)", href)
        if match:
            uri = match.group(1)
            title_elem = link.select_one("p.title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            lessons.append({
                "uri": uri,
                "title": title
            })

    return lessons


def fetch_lesson(uri: str, lang: str) -> Optional[dict]:
    """Fetch a single lesson's content."""
    church_lang = LANG_MAP.get(lang, lang)
    params = {"lang": church_lang, "uri": uri}
    resp = requests.get(CHURCH_API, params=params, timeout=30)

    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    data = resp.json()

    body = data.get("content", {}).get("body", "")
    soup = BeautifulSoup(body, "html.parser")

    # Extract metadata from the kicker/header area
    kicker = soup.select_one(".kicker")

    # Try to extract date range and scripture reference from title/kicker
    full_text = soup.get_text(" ", strip=True)

    # Find date range pattern like "December 29–January 4" or "29 diciembre – 4 enero"
    date_match = re.search(
        r"(\d{1,2}\s+\w+\s*[–-]\s*\d{1,2}\s+\w+|\w+\s+\d{1,2}[–-]\w*\s*\d{1,2})",
        full_text[:200]
    )
    date_range = date_match.group(1) if date_match else ""

    # Extract lesson title (usually after the date in the header)
    header = soup.select_one("header")
    title = ""
    if header:
        title_elem = header.select_one("h1, h2, .title")
        if title_elem:
            title = title_elem.get_text(strip=True)

    # Extract all sections
    sections = []
    for section in soup.select("section"):
        section_title_elem = section.select_one("h2, h3")
        section_title = section_title_elem.get_text(strip=True) if section_title_elem else ""

        # Get paragraphs in this section
        paragraphs = []
        for p in section.select("p"):
            text = p.get_text(" ", strip=True)
            if text and text != section_title:
                paragraphs.append(text)

        if paragraphs:
            sections.append({
                "title": section_title,
                "paragraphs": paragraphs
            })

    # Also get any paragraphs outside sections (intro text)
    intro_paragraphs = []
    for p in soup.select("header ~ p"):
        text = p.get_text(" ", strip=True)
        if text:
            intro_paragraphs.append(text)

    # Get scripture references mentioned
    scripture_refs = []
    for ref in soup.select("a.scripture-ref"):
        scripture_refs.append(ref.get_text(strip=True))

    # Get the full plain text for embedding
    plain_text = soup.get_text("\n", strip=True)

    return {
        "uri": uri,
        "title": title,
        "date_range": date_range,
        "intro": intro_paragraphs,
        "sections": sections,
        "scripture_refs": scripture_refs[:20],  # Limit to first 20
        "plain_text": plain_text,
    }


def fetch_cfm_manual(year: int, lang: str = "en") -> dict:
    """Fetch all lessons for a Come Follow Me manual."""
    manual_info = CFM_MANUALS.get(year)
    if not manual_info:
        raise ValueError(f"No CFM manual defined for year {year}")

    scripture, format_type, short_code = manual_info
    manual_uri = f"/manual/come-follow-me-for-{format_type}-{scripture}-{year}"

    print(f"Fetching TOC from {manual_uri}...")
    lessons = get_lesson_uris(manual_uri, lang)
    print(f"Found {len(lessons)} lessons")

    result = {
        "year": year,
        "scripture": scripture,
        "short_code": short_code,
        "format": format_type,
        "lang": lang,
        "manual_uri": manual_uri,
        "lessons": {}
    }

    for i, lesson_info in enumerate(lessons, 1):
        uri = lesson_info["uri"]
        # Extract lesson ID from URI
        lesson_id = uri.split("/")[-1]

        print(f"  [{i}/{len(lessons)}] {lesson_info['title'][:50]}...", end="", flush=True)

        try:
            lesson_data = fetch_lesson(uri, lang)
            if lesson_data:
                result["lessons"][lesson_id] = lesson_data
            print(" done")
        except Exception as e:
            print(f" ERROR: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return result


def save_cfm(data: dict, lang: str, year: int):
    """Save CFM data to JSON file."""
    output_dir = OUTPUT_DIR / lang
    output_dir.mkdir(parents=True, exist_ok=True)

    short_code = data.get("short_code", "")
    output_file = output_dir / f"cfm_{short_code}_{year}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fetch Come Follow Me content")
    parser.add_argument("--lang", choices=["en", "es", "both"], default="both",
                        help="Language to fetch (default: both)")
    parser.add_argument("--year", type=int, default=2026,
                        help="Year to fetch (default: 2026)")
    parser.add_argument("--test", action="store_true",
                        help="Test mode: fetch only first 5 lessons")
    args = parser.parse_args()

    languages = ["en", "es"] if args.lang == "both" else [args.lang]

    for lang in languages:
        print("=" * 60)
        print(f"FETCHING COME FOLLOW ME {args.year} ({lang.upper()})")
        print("=" * 60)

        data = fetch_cfm_manual(args.year, lang)

        if args.test:
            # Limit to first 5 lessons for testing
            lesson_ids = list(data["lessons"].keys())[:5]
            data["lessons"] = {k: data["lessons"][k] for k in lesson_ids}

        save_cfm(data, lang, args.year)
        print()

    print("=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
