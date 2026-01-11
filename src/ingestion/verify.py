#!/usr/bin/env python3
"""Verify ingested data.

This script validates the integrity of ingested scripture and CFM data by:
1. Counting scriptures by volume and language
2. Counting CFM lessons by year and language
3. Performing random verse spot-checks
4. Validating footnotes data

Expected counts:
| Volume              | EN     | ES     |
|---------------------|--------|--------|
| Old Testament       | 23,145 | 23,145 |
| New Testament       | 7,957  | 7,958  |
| Book of Mormon      | 6,604  | 6,604  |
| D&C                 | 3,654  | 3,654  |
| Pearl of Great Price| 635    | 635    |
| Total Scriptures    | 41,995 | 41,996 |
| CFM Lessons (year)  | 52     | 52     |
"""

from sqlalchemy import text

from src.db import get_session


def verify_scripture_counts(session) -> None:
    """Print scripture counts by volume and language.

    Args:
        session: SQLAlchemy session object
    """
    print("\n=== Scripture Counts ===")
    result = session.execute(
        text("""
        SELECT volume, lang, COUNT(*) as count
        FROM scriptures
        GROUP BY volume, lang
        ORDER BY volume, lang
    """)
    )
    for row in result:
        print(f"  {row.volume:25} {row.lang}: {row.count:,}")

    # Total by language
    result = session.execute(
        text("""
        SELECT lang, COUNT(*) as count FROM scriptures GROUP BY lang ORDER BY lang
    """)
    )
    print("\n  Totals:")
    for row in result:
        print(f"    {row.lang}: {row.count:,}")


def verify_cfm_counts(session) -> None:
    """Print CFM lesson counts by year and language.

    Args:
        session: SQLAlchemy session object
    """
    print("\n=== CFM Lesson Counts ===")
    result = session.execute(
        text("""
        SELECT year, lang, COUNT(*) as count
        FROM cfm_lessons
        GROUP BY year, lang
        ORDER BY year, lang
    """)
    )
    rows = list(result)
    if not rows:
        print("  No CFM lessons found.")
    else:
        for row in rows:
            print(f"  {row.year} {row.lang}: {row.count}")


def random_verse_check(session, count: int = 5) -> None:
    """Select random verses for spot-checking.

    Args:
        session: SQLAlchemy session object
        count: Number of random verses to display (default: 5)
    """
    print(f"\n=== Random Verse Spot-Check ({count} verses) ===")
    result = session.execute(
        text("""
        SELECT volume, book, chapter, verse, lang,
               LEFT(text, 100) as text_preview,
               footnotes IS NOT NULL as has_footnotes
        FROM scriptures
        ORDER BY RANDOM()
        LIMIT :n
    """),
        {"n": count},
    )
    rows = list(result)
    if not rows:
        print("  No scriptures found for spot-check.")
    else:
        for row in rows:
            print(f"\n  {row.volume}/{row.book} {row.chapter}:{row.verse} ({row.lang})")
            print(f"    {row.text_preview}...")
            print(f"    Has footnotes: {row.has_footnotes}")


def footnotes_check(session) -> None:
    """Check footnotes integrity.

    Args:
        session: SQLAlchemy session object
    """
    print("\n=== Footnotes Check ===")
    result = session.execute(
        text("""
        SELECT COUNT(*) FROM scriptures WHERE footnotes IS NOT NULL
    """)
    )
    count = result.scalar()
    print(f"  Verses with footnotes: {count:,}")

    if count == 0:
        print("  No footnotes found to sample.")
        return

    # Sample footnotes
    result = session.execute(
        text("""
        SELECT book, chapter, verse, footnotes
        FROM scriptures
        WHERE footnotes IS NOT NULL
        LIMIT 3
    """)
    )
    print("  Sample footnotes:")
    for row in result:
        footnotes_str = str(row.footnotes)[:80]
        print(f"    {row.book} {row.chapter}:{row.verse}: {footnotes_str}...")


def main() -> None:
    """Run all verification checks."""
    print("Starting data verification...")
    with get_session() as session:
        verify_scripture_counts(session)
        verify_cfm_counts(session)
        random_verse_check(session)
        footnotes_check(session)
    print("\n=== Verification Complete ===")


if __name__ == "__main__":
    main()
