#!/usr/bin/env python3
"""Fetch scriptures from Open Scripture API (English) and Church API (Spanish).

This script fetches all LDS scriptures with footnotes from:
- English: Open Scripture API (openscriptureapi.org)
- Spanish: Church of Jesus Christ content API

Output is saved to JSON files for later import into PostgreSQL.
"""

import json
import time
import requests
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
import re

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "content" / "processed" / "scriptures"

# API endpoints
OPEN_SCRIPTURE_API = "https://openscriptureapi.org/api/scriptures/v1/lds/en"
CHURCH_API = "https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content"

# Rate limiting
RATE_LIMIT_DELAY = 0.15  # seconds between requests


def fetch_english_volume(volume_id: str) -> dict:
    """Fetch volume metadata including books list."""
    url = f"{OPEN_SCRIPTURE_API}/volume/{volume_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_english_book(volume_id: str, book_id: str) -> dict:
    """Fetch book metadata including chapter list."""
    url = f"{OPEN_SCRIPTURE_API}/volume/{volume_id}/{book_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_english_chapter(volume_id: str, book_id: str, chapter: int) -> dict:
    """Fetch a single chapter with verses and footnotes."""
    url = f"{OPEN_SCRIPTURE_API}/volume/{volume_id}/{book_id}/{chapter}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_all_english(volumes: Optional[list] = None) -> dict:
    """Fetch all English scriptures from Open Scripture API.

    Returns dict with structure:
    {
        "volume_id": {
            "title": "Old Testament",
            "books": {
                "genesis": {
                    "title": "Genesis",
                    "chapters": {
                        1: {
                            "summary": "...",
                            "verses": [{"text": "...", "footnotes": [...]}]
                        }
                    }
                }
            }
        }
    }
    """
    if volumes is None:
        volumes = [
            "oldtestament",
            "newtestament",
            "bookofmormon",
            "doctrineandcovenants",
            "pearlofgreatprice",
        ]

    result = {}

    for volume_id in volumes:
        print(f"\nFetching {volume_id}...")
        vol_data = fetch_english_volume(volume_id)

        result[volume_id] = {
            "title": vol_data.get("title", volume_id),
            "books": {}
        }

        for book in vol_data.get("books", []):
            book_id = book["_id"]
            book_title = book.get("title", book_id)

            # Fetch book to get chapter list
            book_data = fetch_english_book(volume_id, book_id)
            chapters = book_data.get("chapters", [])
            num_chapters = len(chapters)
            time.sleep(RATE_LIMIT_DELAY)

            print(f"  {book_title} ({num_chapters} chapters)...", end="", flush=True)

            result[volume_id]["books"][book_id] = {
                "title": book_title,
                "chapters": {}
            }

            for chapter_num in range(1, num_chapters + 1):
                try:
                    chapter_data = fetch_english_chapter(volume_id, book_id, chapter_num)
                    chapter_info = chapter_data.get("chapter", {})

                    result[volume_id]["books"][book_id]["chapters"][chapter_num] = {
                        "summary": chapter_info.get("summary", ""),
                        "verses": chapter_info.get("verses", [])
                    }

                    time.sleep(RATE_LIMIT_DELAY)
                except Exception as e:
                    print(f"\n    Error fetching {book_id} {chapter_num}: {e}")

            print(" done")

    return result


def parse_spanish_chapter(html: str) -> dict:
    """Parse Spanish chapter HTML into structured data."""
    soup = BeautifulSoup(html, "html.parser")

    # Get chapter summary
    summary_elem = soup.select_one(".study-summary")
    summary = summary_elem.get_text(strip=True) if summary_elem else ""

    # Parse verses
    verses = []
    for verse_elem in soup.select("p.verse"):
        # Get verse number
        verse_num_elem = verse_elem.select_one(".verse-number")
        if not verse_num_elem:
            continue

        verse_num_text = verse_num_elem.get_text(strip=True)
        try:
            verse_num = int(re.sub(r'\D', '', verse_num_text))
        except ValueError:
            continue

        # Get footnote markers and their positions
        footnotes = []
        for marker in verse_elem.select("sup.marker"):
            marker_value = marker.get("data-value", "")
            # Find the parent anchor to get the note ID
            parent_a = marker.find_parent("a", class_="study-note-ref")
            if parent_a:
                note_id = parent_a.get("href", "").lstrip("#")
                footnotes.append({
                    "marker": marker_value,
                    "note_id": note_id
                })

        # Get clean verse text (remove markers)
        # Clone the element to avoid modifying original
        verse_copy = BeautifulSoup(str(verse_elem), "html.parser").select_one("p.verse")
        for marker in verse_copy.select("sup.marker"):
            marker.decompose()
        for num in verse_copy.select(".verse-number"):
            num.decompose()

        text = verse_copy.get_text(" ", strip=True)
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()

        verses.append({
            "verse": verse_num,
            "text": text,
            "footnote_markers": footnotes
        })

    # Parse footnotes from footer
    footnote_refs = {}
    for note in soup.select("footer.study-notes li[data-marker]"):
        note_id = note.get("id", "")
        marker = note.get("data-marker", "")
        content_elem = note.select_one("p")
        content = content_elem.get_text(strip=True) if content_elem else ""

        if note_id:
            footnote_refs[note_id] = {
                "marker": marker,
                "content": content
            }

    # Attach footnote content to verses
    for verse in verses:
        for fn in verse.get("footnote_markers", []):
            note_id = fn.get("note_id", "")
            if note_id in footnote_refs:
                fn["footnote"] = footnote_refs[note_id]["content"]

    return {
        "summary": summary,
        "verses": verses
    }


def fetch_spanish_chapter(uri: str) -> Optional[dict]:
    """Fetch a single Spanish chapter from Church API."""
    params = {"lang": "spa", "uri": uri}
    resp = requests.get(CHURCH_API, params=params, timeout=30)

    if resp.status_code == 404:
        return None

    resp.raise_for_status()
    data = resp.json()

    html = data.get("content", {}).get("body", "")
    if not html:
        return None

    return parse_spanish_chapter(html)


# Spanish scripture URI mappings
SPANISH_BOOKS = {
    "oldtestament": {
        "uri_prefix": "/scriptures/ot",
        "books": [
            ("gen", "Génesis", 50),
            ("ex", "Éxodo", 40),
            ("lev", "Levítico", 27),
            ("num", "Números", 36),
            ("deut", "Deuteronomio", 34),
            ("josh", "Josué", 24),
            ("judg", "Jueces", 21),
            ("ruth", "Rut", 4),
            ("1-sam", "1 Samuel", 31),
            ("2-sam", "2 Samuel", 24),
            ("1-kgs", "1 Reyes", 22),
            ("2-kgs", "2 Reyes", 25),
            ("1-chr", "1 Crónicas", 29),
            ("2-chr", "2 Crónicas", 36),
            ("ezra", "Esdras", 10),
            ("neh", "Nehemías", 13),
            ("esth", "Ester", 10),
            ("job", "Job", 42),
            ("ps", "Salmos", 150),
            ("prov", "Proverbios", 31),
            ("eccl", "Eclesiastés", 12),
            ("song", "Cantares", 8),
            ("isa", "Isaías", 66),
            ("jer", "Jeremías", 52),
            ("lam", "Lamentaciones", 5),
            ("ezek", "Ezequiel", 48),
            ("dan", "Daniel", 12),
            ("hosea", "Oseas", 14),
            ("joel", "Joel", 3),
            ("amos", "Amós", 9),
            ("obad", "Abdías", 1),
            ("jonah", "Jonás", 4),
            ("micah", "Miqueas", 7),
            ("nahum", "Nahúm", 3),
            ("hab", "Habacuc", 3),
            ("zeph", "Sofonías", 3),
            ("hag", "Hageo", 2),
            ("zech", "Zacarías", 14),
            ("mal", "Malaquías", 4),
        ]
    },
    "newtestament": {
        "uri_prefix": "/scriptures/nt",
        "books": [
            ("matt", "Mateo", 28),
            ("mark", "Marcos", 16),
            ("luke", "Lucas", 24),
            ("john", "Juan", 21),
            ("acts", "Hechos", 28),
            ("rom", "Romanos", 16),
            ("1-cor", "1 Corintios", 16),
            ("2-cor", "2 Corintios", 13),
            ("gal", "Gálatas", 6),
            ("eph", "Efesios", 6),
            ("philip", "Filipenses", 4),
            ("col", "Colosenses", 4),
            ("1-thes", "1 Tesalonicenses", 5),
            ("2-thes", "2 Tesalonicenses", 3),
            ("1-tim", "1 Timoteo", 6),
            ("2-tim", "2 Timoteo", 4),
            ("titus", "Tito", 3),
            ("philem", "Filemón", 1),
            ("heb", "Hebreos", 13),
            ("james", "Santiago", 5),
            ("1-pet", "1 Pedro", 5),
            ("2-pet", "2 Pedro", 3),
            ("1-jn", "1 Juan", 5),
            ("2-jn", "2 Juan", 1),
            ("3-jn", "3 Juan", 1),
            ("jude", "Judas", 1),
            ("rev", "Apocalipsis", 22),
        ]
    },
    "bookofmormon": {
        "uri_prefix": "/scriptures/bofm",
        "books": [
            ("1-ne", "1 Nefi", 22),
            ("2-ne", "2 Nefi", 33),
            ("jacob", "Jacob", 7),
            ("enos", "Enós", 1),
            ("jarom", "Jarom", 1),
            ("omni", "Omni", 1),
            ("w-of-m", "Palabras de Mormón", 1),
            ("mosiah", "Mosíah", 29),
            ("alma", "Alma", 63),
            ("hel", "Helamán", 16),
            ("3-ne", "3 Nefi", 30),
            ("4-ne", "4 Nefi", 1),
            ("morm", "Mormón", 9),
            ("ether", "Éter", 15),
            ("moro", "Moroni", 10),
        ]
    },
    "doctrineandcovenants": {
        "uri_prefix": "/scriptures/dc-testament/dc",
        "books": [
            # D&C uses sections, not books
        ]
    },
    "pearlofgreatprice": {
        "uri_prefix": "/scriptures/pgp",
        "books": [
            ("moses", "Moisés", 8),
            ("abr", "Abraham", 5),
            ("js-m", "José Smith—Mateo", 1),
            ("js-h", "José Smith—Historia", 1),
            ("a-of-f", "Artículos de Fe", 1),
        ]
    },
}


def fetch_all_spanish(volumes: Optional[list] = None) -> dict:
    """Fetch all Spanish scriptures from Church API."""
    if volumes is None:
        volumes = list(SPANISH_BOOKS.keys())

    result = {}

    for volume_id in volumes:
        if volume_id not in SPANISH_BOOKS:
            continue

        vol_info = SPANISH_BOOKS[volume_id]
        uri_prefix = vol_info["uri_prefix"]

        print(f"\nFetching {volume_id} (Spanish)...")

        result[volume_id] = {
            "title": volume_id,
            "books": {}
        }

        # Special handling for D&C (sections, not books)
        if volume_id == "doctrineandcovenants":
            print(f"  Doctrine and Covenants (138 sections)...", end="", flush=True)
            result[volume_id]["books"]["dc"] = {
                "title": "Doctrina y Convenios",
                "chapters": {}
            }

            for section in range(1, 139):
                uri = f"{uri_prefix}/{section}"
                try:
                    chapter_data = fetch_spanish_chapter(uri)
                    if chapter_data:
                        result[volume_id]["books"]["dc"]["chapters"][section] = chapter_data
                    time.sleep(RATE_LIMIT_DELAY)
                except Exception as e:
                    print(f"\n    Error fetching D&C {section}: {e}")

            # Official Declaration 1 and 2
            for od in [1, 2]:
                uri = f"/scriptures/dc-testament/od/{od}"
                try:
                    od_data = fetch_spanish_chapter(uri)
                    if od_data:
                        result[volume_id]["books"]["dc"]["chapters"][f"od{od}"] = od_data
                    time.sleep(RATE_LIMIT_DELAY)
                except Exception as e:
                    print(f"\n    Error fetching OD {od}: {e}")

            print(" done")
            continue

        for book_id, book_title, num_chapters in vol_info["books"]:
            print(f"  {book_title} ({num_chapters} chapters)...", end="", flush=True)

            result[volume_id]["books"][book_id] = {
                "title": book_title,
                "chapters": {}
            }

            for chapter_num in range(1, num_chapters + 1):
                uri = f"{uri_prefix}/{book_id}/{chapter_num}"
                try:
                    chapter_data = fetch_spanish_chapter(uri)
                    if chapter_data:
                        result[volume_id]["books"][book_id]["chapters"][chapter_num] = chapter_data
                    time.sleep(RATE_LIMIT_DELAY)
                except Exception as e:
                    print(f"\n    Error fetching {book_id} {chapter_num}: {e}")

            print(" done")

    return result


def save_scriptures(data: dict, lang: str):
    """Save scriptures to JSON file."""
    output_dir = OUTPUT_DIR / lang
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save each volume separately
    for volume_id, volume_data in data.items():
        output_file = output_dir / f"{volume_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(volume_data, f, ensure_ascii=False, indent=2)
        print(f"Saved {output_file}")

    # Also save combined file
    combined_file = output_dir / "all_scriptures.json"
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {combined_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Fetch LDS scriptures")
    parser.add_argument("--lang", choices=["en", "es", "both"], default="both",
                        help="Language to fetch (default: both)")
    parser.add_argument("--volume", type=str, help="Specific volume to fetch")
    parser.add_argument("--test", action="store_true",
                        help="Test mode: fetch only Genesis/1 Nephi")
    args = parser.parse_args()

    volumes = None
    if args.volume:
        volumes = [args.volume]
    elif args.test:
        volumes = ["oldtestament"]  # Just OT for testing

    if args.lang in ["en", "both"]:
        print("=" * 60)
        print("FETCHING ENGLISH SCRIPTURES (Open Scripture API)")
        print("=" * 60)

        if args.test:
            # Test: just fetch Genesis
            print("\nTest mode: fetching only Genesis...")
            en_data = {"oldtestament": {"title": "Old Testament", "books": {}}}
            vol_data = fetch_english_volume("oldtestament")
            genesis = next((b for b in vol_data["books"] if b["_id"] == "genesis"), None)
            if genesis:
                en_data["oldtestament"]["books"]["genesis"] = {
                    "title": "Genesis",
                    "chapters": {}
                }
                for ch in range(1, 51):  # Genesis has 50 chapters
                    try:
                        ch_data = fetch_english_chapter("oldtestament", "genesis", ch)
                        en_data["oldtestament"]["books"]["genesis"]["chapters"][ch] = {
                            "summary": ch_data.get("chapter", {}).get("summary", ""),
                            "verses": ch_data.get("chapter", {}).get("verses", [])
                        }
                        print(f"  Genesis {ch}...", end="\r")
                        time.sleep(RATE_LIMIT_DELAY)
                    except Exception as e:
                        print(f"  Error: Genesis {ch}: {e}")
                print("  Genesis complete!          ")
        else:
            en_data = fetch_all_english(volumes)

        save_scriptures(en_data, "en")

    if args.lang in ["es", "both"]:
        print("\n" + "=" * 60)
        print("FETCHING SPANISH SCRIPTURES (Church API)")
        print("=" * 60)

        if args.test:
            # Test: just fetch Génesis
            print("\nTest mode: fetching only Génesis...")
            es_data = {"oldtestament": {"title": "Antiguo Testamento", "books": {}}}
            es_data["oldtestament"]["books"]["gen"] = {
                "title": "Génesis",
                "chapters": {}
            }
            for ch in range(1, 51):
                uri = f"/scriptures/ot/gen/{ch}"
                try:
                    ch_data = fetch_spanish_chapter(uri)
                    if ch_data:
                        es_data["oldtestament"]["books"]["gen"]["chapters"][ch] = ch_data
                    print(f"  Génesis {ch}...", end="\r")
                    time.sleep(RATE_LIMIT_DELAY)
                except Exception as e:
                    print(f"  Error: Génesis {ch}: {e}")
            print("  Génesis complete!          ")
        else:
            es_data = fetch_all_spanish(volumes)

        save_scriptures(es_data, "es")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
