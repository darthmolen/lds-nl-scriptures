#!/usr/bin/env python3
"""Ingest Come Follow Me lessons into the database.

This script loads CFM lessons from JSON files into the cfm_lessons table.
Each year focuses on a specific testament:
- 2023: New Testament
- 2024: Book of Mormon
- 2025: Doctrine & Covenants
- 2026: Old Testament

Usage:
    python -m src.ingestion.ingest_cfm --year 2024 --lang en
    python -m src.ingestion.ingest_cfm --year 2024 --lang en --force
"""

import argparse
import json
import sys
from pathlib import Path

from src.db import CFMLesson, get_session
from src.ingestion.base import check_or_skip_cfm

# Year to testament mapping with corresponding JSON filenames
YEAR_TESTAMENT_MAP = {
    2023: ("nt", "cfm_nt_2023.json"),
    2024: ("bom", "cfm_bom_2024.json"),
    2025: ("dc", "cfm_dc_2025.json"),
    2026: ("ot", "cfm_ot_2026.json"),
}


def create_cfm_year_parser() -> argparse.ArgumentParser:
    """Create CLI parser for CFM lesson ingestion.

    Returns:
        ArgumentParser configured with --year, --lang, and --force options.
    """
    parser = argparse.ArgumentParser(
        description="Ingest Come Follow Me lessons into database"
    )
    parser.add_argument(
        "--year",
        type=int,
        choices=list(YEAR_TESTAMENT_MAP.keys()),
        required=True,
        help="Lesson year (2023=NT, 2024=BoM, 2025=D&C, 2026=OT)",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "es"],
        required=True,
        help="Language to ingest (en=English, es=Spanish)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Truncate existing data before loading",
    )
    return parser


def main() -> None:
    """Main entry point for CFM ingestion."""
    parser = create_cfm_year_parser()
    args = parser.parse_args()

    testament, filename = YEAR_TESTAMENT_MAP[args.year]
    json_path = Path(f"content/processed/cfm/{args.lang}/{filename}")

    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}")
        sys.exit(1)

    with get_session() as session:
        if not check_or_skip_cfm(session, args.year, args.lang, args.force):
            return

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for lesson_id, lesson in data["lessons"].items():
            cfm = CFMLesson(
                year=args.year,
                testament=testament,
                lesson_id=lesson_id,
                title=lesson.get("title", ""),
                date_range=lesson.get("date_range", ""),
                scripture_refs=lesson.get("scripture_refs", []),
                content=lesson.get("plain_text", ""),
                lang=args.lang,
            )
            session.add(cfm)
            count += 1

        session.commit()
        print(f"Loaded {count} lessons for CFM {args.year}/{args.lang}")


if __name__ == "__main__":
    main()
