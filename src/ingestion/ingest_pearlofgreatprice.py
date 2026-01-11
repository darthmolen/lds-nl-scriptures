#!/usr/bin/env python3
"""Ingest Pearl of Great Price scriptures into the database."""
import json
from pathlib import Path

from src.db import get_session, Scripture
from src.ingestion.base import create_scripture_parser, check_or_skip

VOLUME = "pearlofgreatprice"


def main():
    """Load Pearl of Great Price verses from JSON into the database."""
    parser = create_scripture_parser(VOLUME)
    args = parser.parse_args()

    with get_session() as session:
        if not check_or_skip(session, VOLUME, args.lang, args.force):
            return

        json_path = Path(f"content/processed/scriptures/{args.lang}/{VOLUME}.json")
        with open(json_path) as f:
            data = json.load(f)

        count = 0
        for book_id, book in data["books"].items():
            for chapter_num, chapter in book["chapters"].items():
                for verse_idx, verse in enumerate(chapter["verses"]):
                    scripture = Scripture(
                        volume=VOLUME,
                        book=book_id,
                        chapter=int(chapter_num),
                        verse=verse_idx + 1,
                        text=verse["text"],
                        lang=args.lang,
                        footnotes=verse.get("footnotes"),
                    )
                    session.add(scripture)
                    count += 1

        session.commit()
        print(f"Loaded {count} verses for {VOLUME}/{args.lang}")


if __name__ == "__main__":
    main()
