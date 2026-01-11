"""Base ingestion utilities for Scripture Search project.

Provides shared functionality for all ingestion scripts including:
- CLI argument parsing for scriptures and CFM lessons
- Data existence checking and truncation
- Common ingestion patterns

Usage:
    from src.ingestion.base import (
        create_scripture_parser,
        check_or_skip,
        create_cfm_parser,
        check_or_skip_cfm,
    )
"""

import argparse
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

# Valid volume names for scriptures
VALID_VOLUMES = (
    "oldtestament",
    "newtestament",
    "bookofmormon",
    "doctrineandcovenants",
    "pearlofgreatprice",
)

# Valid language codes
VALID_LANGUAGES = ("en", "es")

# Valid CFM testament codes
VALID_TESTAMENTS = ("ot", "nt", "bom", "dc")


def create_scripture_parser(volume_name: str) -> argparse.ArgumentParser:
    """Create CLI parser for scripture ingestion scripts.

    Args:
        volume_name: Human-readable name of the scripture volume
                    (e.g., "Old Testament", "Book of Mormon")

    Returns:
        ArgumentParser configured with --lang and --force options.

    Example:
        parser = create_scripture_parser("Book of Mormon")
        args = parser.parse_args()
        # args.lang will be 'en' or 'es'
        # args.force will be True or False
    """
    parser = argparse.ArgumentParser(
        description=f"Ingest {volume_name} scriptures into database"
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


def check_existing_scriptures(session: Session, volume: str, lang: str) -> int:
    """Return count of existing verses for volume+lang.

    Args:
        session: SQLAlchemy session
        volume: Scripture volume name (e.g., 'bookofmormon')
        lang: Language code ('en' or 'es')

    Returns:
        Count of verses matching the volume and language.
    """
    result = session.execute(
        text("SELECT COUNT(*) FROM scriptures WHERE volume = :v AND lang = :l"),
        {"v": volume, "l": lang},
    )
    return result.scalar() or 0


def truncate_scriptures(session: Session, volume: str, lang: str) -> int:
    """Delete all verses for volume+lang.

    Args:
        session: SQLAlchemy session
        volume: Scripture volume name (e.g., 'bookofmormon')
        lang: Language code ('en' or 'es')

    Returns:
        Number of deleted rows.

    Note:
        Commits the transaction after deletion.
    """
    result = session.execute(
        text("DELETE FROM scriptures WHERE volume = :v AND lang = :l"),
        {"v": volume, "l": lang},
    )
    session.commit()
    return result.rowcount or 0


def check_or_skip(
    session: Session, volume: str, lang: str, force: bool
) -> bool:
    """Check existing data and determine whether to proceed with ingestion.

    If data exists for the volume/lang combination:
    - Without --force: prints a message and returns False (skip)
    - With --force: truncates existing data and returns True (proceed)

    If no data exists, returns True (proceed).

    Args:
        session: SQLAlchemy session
        volume: Scripture volume name (e.g., 'bookofmormon')
        lang: Language code ('en' or 'es')
        force: If True, truncate existing data and proceed

    Returns:
        True if ingestion should proceed, False to skip.

    Example:
        with get_session() as session:
            if not check_or_skip(session, 'bookofmormon', 'en', args.force):
                sys.exit(0)
            # Proceed with ingestion...
    """
    count = check_existing_scriptures(session, volume, lang)
    if count > 0 and not force:
        print(f"Found {count} verses for {volume}/{lang}. Use --force to reload.")
        return False
    if force and count > 0:
        deleted = truncate_scriptures(session, volume, lang)
        print(f"Truncated {deleted} existing verses for {volume}/{lang}")
    return True


# -----------------------------------------------------------------------------
# CFM (Come Follow Me) Ingestion Utilities
# -----------------------------------------------------------------------------


def create_cfm_parser() -> argparse.ArgumentParser:
    """Create CLI parser for CFM lesson ingestion scripts.

    Returns:
        ArgumentParser configured with --year, --lang, --testament, and --force options.

    Example:
        parser = create_cfm_parser()
        args = parser.parse_args()
        # args.year will be an integer (e.g., 2024)
        # args.lang will be 'en' or 'es'
        # args.testament will be 'ot', 'nt', 'bom', or 'dc'
        # args.force will be True or False
    """
    parser = argparse.ArgumentParser(
        description="Ingest Come Follow Me lessons into database"
    )
    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Lesson year (e.g., 2024, 2025)",
    )
    parser.add_argument(
        "--lang",
        choices=["en", "es"],
        required=True,
        help="Language to ingest (en=English, es=Spanish)",
    )
    parser.add_argument(
        "--testament",
        choices=["ot", "nt", "bom", "dc"],
        required=True,
        help="Testament focus (ot=OT, nt=NT, bom=BoM, dc=D&C)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Truncate existing data before loading",
    )
    return parser


def check_existing_cfm(session: Session, year: int, lang: str) -> int:
    """Return count of existing CFM lessons for year+lang.

    Args:
        session: SQLAlchemy session
        year: Lesson year (e.g., 2024)
        lang: Language code ('en' or 'es')

    Returns:
        Count of lessons matching the year and language.
    """
    result = session.execute(
        text("SELECT COUNT(*) FROM cfm_lessons WHERE year = :y AND lang = :l"),
        {"y": year, "l": lang},
    )
    return result.scalar() or 0


def truncate_cfm(session: Session, year: int, lang: str) -> int:
    """Delete all CFM lessons for year+lang.

    Args:
        session: SQLAlchemy session
        year: Lesson year (e.g., 2024)
        lang: Language code ('en' or 'es')

    Returns:
        Number of deleted rows.

    Note:
        Commits the transaction after deletion.
    """
    result = session.execute(
        text("DELETE FROM cfm_lessons WHERE year = :y AND lang = :l"),
        {"y": year, "l": lang},
    )
    session.commit()
    return result.rowcount or 0


def check_or_skip_cfm(
    session: Session, year: int, lang: str, force: bool
) -> bool:
    """Check existing CFM data and determine whether to proceed with ingestion.

    If data exists for the year/lang combination:
    - Without --force: prints a message and returns False (skip)
    - With --force: truncates existing data and returns True (proceed)

    If no data exists, returns True (proceed).

    Args:
        session: SQLAlchemy session
        year: Lesson year (e.g., 2024)
        lang: Language code ('en' or 'es')
        force: If True, truncate existing data and proceed

    Returns:
        True if ingestion should proceed, False to skip.

    Example:
        with get_session() as session:
            if not check_or_skip_cfm(session, 2024, 'en', args.force):
                sys.exit(0)
            # Proceed with ingestion...
    """
    count = check_existing_cfm(session, year, lang)
    if count > 0 and not force:
        print(f"Found {count} lessons for CFM {year}/{lang}. Use --force to reload.")
        return False
    if force and count > 0:
        deleted = truncate_cfm(session, year, lang)
        print(f"Truncated {deleted} existing lessons for CFM {year}/{lang}")
    return True
