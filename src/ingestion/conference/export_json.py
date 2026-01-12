#!/usr/bin/env python3
"""Export conference paragraphs to JSON format.

Exports conference data from the database to JSON files, organized by
year and month, for subsequent TOON conversion.

Usage:
    # Single conference:
    python -m src.ingestion.conference.export_json --year 2024 --month 10 --lang en

    # All conferences:
    python -m src.ingestion.conference.export_json --all --lang en

Output: content/processed/conference/{lang}/{year}_{month}.json
"""

import argparse
import json
from pathlib import Path
from typing import Optional

from sqlalchemy import text

from src.db import get_session


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Export conference paragraphs to JSON"
    )
    parser.add_argument("--year", type=int, help="Conference year")
    parser.add_argument("--month", choices=["04", "10"], help="Conference month")
    parser.add_argument("--all", action="store_true", help="Export all conferences")
    parser.add_argument("--lang", choices=["en", "es"], required=True)
    return parser


def export_conference(session, year: int, month: str, lang: str, output_dir: Path) -> int:
    """Export a single conference to JSON.

    Returns number of paragraphs exported.
    """
    # Query all paragraphs for this conference
    result = session.execute(
        text("""
            SELECT
                id, year, month, session, talk_uri, talk_title,
                speaker_name, speaker_role, paragraph_num, text,
                footnotes, scripture_refs, talk_refs
            FROM conference_paragraphs
            WHERE year = :y AND month = :m AND lang = :l
            ORDER BY talk_uri, paragraph_num
        """),
        {"y": year, "m": month, "l": lang},
    )
    rows = result.fetchall()

    if not rows:
        return 0

    # Organize by talk
    talks = {}
    for row in rows:
        uri = row.talk_uri
        if uri not in talks:
            talks[uri] = {
                "uri": uri,
                "title": row.talk_title,
                "speaker_name": row.speaker_name,
                "speaker_role": row.speaker_role,
                "paragraphs": [],
            }
        talks[uri]["paragraphs"].append({
            "num": row.paragraph_num,
            "text": row.text,
            "footnotes": row.footnotes,
            "scripture_refs": row.scripture_refs,
            "talk_refs": row.talk_refs,
        })

    # Build output structure
    data = {
        "year": year,
        "month": month,
        "lang": lang,
        "talk_count": len(talks),
        "paragraph_count": len(rows),
        "talks": list(talks.values()),
    }

    # Write to file
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{year}_{month}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Exported {len(rows)} paragraphs to {output_file}")
    return len(rows)


def get_available_conferences(session, lang: str) -> list[tuple[int, str]]:
    """Get list of conferences with data in database."""
    result = session.execute(
        text("""
            SELECT DISTINCT year, month
            FROM conference_paragraphs
            WHERE lang = :l
            ORDER BY year, month
        """),
        {"l": lang},
    )
    return [(row.year, row.month) for row in result.fetchall()]


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    output_dir = Path(f"content/processed/conference/{args.lang}")

    with get_session() as session:
        if args.all:
            conferences = get_available_conferences(session, args.lang)
            if not conferences:
                print(f"No conference data found for {args.lang}")
                return
        elif args.year and args.month:
            conferences = [(args.year, args.month)]
        else:
            parser.error("Must specify either --all or both --year and --month")
            return

        print(f"Exporting {len(conferences)} conferences for {args.lang}...")

        total = 0
        for year, month in conferences:
            print(f"\n[{year}/{month}]")
            count = export_conference(session, year, month, args.lang, output_dir)
            total += count

        print(f"\nDone! Total paragraphs exported: {total}")


if __name__ == "__main__":
    main()
