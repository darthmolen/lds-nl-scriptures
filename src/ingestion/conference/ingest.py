#!/usr/bin/env python3
"""Ingest General Conference talks into the database.

This script fetches conference talks from the Church API, parses them
into paragraphs, and stores them in the conference_paragraphs table.

Usage:
    # Single conference:
    python -m src.ingestion.conference.ingest --year 2024 --month 10 --lang en

    # All conferences:
    python -m src.ingestion.conference.ingest --all --lang en

    # Force reload:
    python -m src.ingestion.conference.ingest --year 2024 --month 10 --lang en --force
"""

import argparse
import sys
from typing import Optional

from sqlalchemy import text

from src.db import get_session, ConferenceParagraph
from src.ingestion.conference.client import ChurchAPIClient, get_all_conferences
from src.ingestion.conference.parser import parse_talk, get_content_paragraphs

# Language code mapping (database uses 'en'/'es', API uses 'eng'/'spa')
LANG_MAP = {"en": "eng", "es": "spa"}


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Ingest General Conference talks into database"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Conference year (2014-2025)",
    )
    parser.add_argument(
        "--month",
        choices=["04", "10"],
        help="Conference month (04=April, 10=October)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ingest all conferences (2014-2025)",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "es"],
        required=True,
        help="Language to ingest",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Truncate existing data before loading",
    )
    return parser


def check_existing(session, year: int, month: str, lang: str) -> int:
    """Return count of existing paragraphs for conference."""
    result = session.execute(
        text("""
            SELECT COUNT(*) FROM conference_paragraphs
            WHERE year = :y AND month = :m AND lang = :l
        """),
        {"y": year, "m": month, "l": lang},
    )
    return result.scalar() or 0


def truncate_conference(session, year: int, month: str, lang: str) -> int:
    """Delete existing data for conference."""
    result = session.execute(
        text("""
            DELETE FROM conference_paragraphs
            WHERE year = :y AND month = :m AND lang = :l
        """),
        {"y": year, "m": month, "l": lang},
    )
    session.commit()
    return result.rowcount or 0


def ingest_conference(
    session,
    client: ChurchAPIClient,
    year: int,
    month: str,
    lang: str,
    force: bool = False,
) -> int:
    """Ingest a single conference.

    Returns number of paragraphs inserted.
    """
    # Check existing data
    count = check_existing(session, year, month, lang)
    if count > 0:
        if not force:
            print(f"  Found {count} paragraphs for {year}/{month}. Use --force to reload.")
            return 0
        deleted = truncate_conference(session, year, month, lang)
        print(f"  Truncated {deleted} existing paragraphs")

    # Fetch conference manifest
    manifest = client.fetch_conference_manifest(year, month)
    print(f"  Found {len(manifest.talks)} talks")

    total_paragraphs = 0

    for i, talk_meta in enumerate(manifest.talks, 1):
        try:
            # Fetch and parse talk
            raw_data = client.fetch_talk(talk_meta.uri)
            parsed = parse_talk(raw_data)

            # Get content paragraphs only (exclude metadata like author/kicker)
            paragraphs = get_content_paragraphs(parsed)

            # Insert paragraphs
            for para in paragraphs:
                # Get footnotes for this paragraph
                para_footnotes = [
                    {"id": fn.note_id, "marker": fn.marker, "text": fn.text, "refs": fn.reference_uris}
                    for fn in parsed.footnotes
                    if fn.paragraph_id == para.paragraph_id
                ]

                cp = ConferenceParagraph(
                    year=year,
                    month=month,
                    session=None,  # TODO: extract from manifest if available
                    talk_uri=talk_meta.uri,
                    talk_title=parsed.title,
                    speaker_name=parsed.speaker_name,
                    speaker_role=parsed.speaker_role,
                    paragraph_num=para.paragraph_num,
                    text=para.text,
                    lang=lang,
                    footnotes=para_footnotes if para_footnotes else None,
                    scripture_refs=parsed.scripture_refs if parsed.scripture_refs else None,
                    talk_refs=parsed.talk_refs if parsed.talk_refs else None,
                )
                session.add(cp)
                total_paragraphs += 1

            if i % 10 == 0:
                session.commit()
                print(f"    Processed {i}/{len(manifest.talks)} talks...")

        except Exception as e:
            print(f"  ERROR on talk {talk_meta.uri}: {e}")
            continue

    session.commit()
    return total_paragraphs


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate arguments
    if args.all:
        conferences = get_all_conferences(2014, 2025)
    elif args.year and args.month:
        conferences = [(args.year, args.month)]
    else:
        parser.error("Must specify either --all or both --year and --month")
        return

    api_lang = LANG_MAP[args.lang]
    client = ChurchAPIClient(lang=api_lang, delay=0.5)

    print(f"Starting conference ingestion for {args.lang}...")
    print(f"Processing {len(conferences)} conferences")

    total = 0

    with get_session() as session:
        for year, month in conferences:
            print(f"\n[{year}/{month}]")
            count = ingest_conference(
                session, client, year, month, args.lang, args.force
            )
            total += count
            print(f"  Inserted {count} paragraphs")

    print(f"\nDone! Total paragraphs inserted: {total}")


if __name__ == "__main__":
    main()
