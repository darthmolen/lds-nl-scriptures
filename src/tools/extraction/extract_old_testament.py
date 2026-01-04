#!/usr/bin/env python3
"""
Phase 1A: Old Testament Extraction

Extracts all 39 Old Testament books from the quad PDF to markdown files.
Uses pymupdf4llm for CPU-friendly extraction.

Usage:
    python extract_old_testament.py
"""

import sys
from pathlib import Path

try:
    import pymupdf4llm
except ImportError:
    print("Error: pymupdf4llm not installed. Run: pip install pymupdf pymupdf4llm")
    sys.exit(1)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PDF_PATH = PROJECT_ROOT / "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = PROJECT_ROOT / "content/processed/scriptures/en/old-testament"

# Old Testament books with page ranges (1-indexed as shown in PDF)
# Format: (filename, start_page, end_page)
BOOKS = [
    ("genesis", 12, 89),
    ("exodus", 90, 156),
    ("leviticus", 157, 200),
    ("numbers", 201, 262),
    ("deuteronomy", 263, 318),
    ("joshua", 319, 353),
    ("judges", 354, 387),
    ("ruth", 388, 392),
    ("1-samuel", 393, 436),
    ("2-samuel", 437, 473),
    ("1-kings", 474, 517),
    ("2-kings", 518, 558),
    ("1-chronicles", 559, 597),
    ("2-chronicles", 598, 644),
    ("ezra", 645, 658),
    ("nehemiah", 659, 678),
    ("esther", 679, 688),
    ("job", 689, 724),
    ("psalms", 725, 821),
    ("proverbs", 822, 855),
    ("ecclesiastes", 856, 866),
    ("song-of-solomon", 867, 871),
    ("isaiah", 872, 952),
    ("jeremiah", 953, 1030),
    ("lamentations", 1031, 1037),
    ("ezekiel", 1038, 1109),
    ("daniel", 1110, 1132),
    ("hosea", 1133, 1143),
    ("joel", 1144, 1147),
    ("amos", 1148, 1156),
    ("obadiah", 1157, 1157),
    ("jonah", 1158, 1160),
    ("micah", 1161, 1166),
    ("nahum", 1167, 1169),
    ("habakkuk", 1170, 1172),
    ("zephaniah", 1173, 1176),
    ("haggai", 1177, 1178),
    ("zechariah", 1179, 1190),
    ("malachi", 1191, 1195),
]


def extract_book(name: str, start_page: int, end_page: int) -> bool:
    """Extract a single book from the PDF to markdown.

    Args:
        name: Book filename (without .md extension)
        start_page: Start page (1-indexed)
        end_page: End page (1-indexed, inclusive)

    Returns:
        True if successful, False otherwise
    """
    output_file = OUTPUT_DIR / f"{name}.md"

    # Skip if already extracted
    if output_file.exists():
        print(f"  Skipping {name} (already exists)")
        return True

    try:
        # Convert to 0-indexed for pymupdf4llm
        pages = list(range(start_page - 1, end_page))
        md = pymupdf4llm.to_markdown(str(PDF_PATH), pages=pages)
        output_file.write_text(md, encoding="utf-8")
        return True
    except Exception as e:
        print(f"  Error extracting {name}: {e}")
        return False


def main():
    """Extract all Old Testament books."""
    print("Phase 1A: Old Testament Extraction")
    print("=" * 40)

    # Verify PDF exists
    if not PDF_PATH.exists():
        print(f"Error: PDF not found at {PDF_PATH}")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Source: {PDF_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Books:  {len(BOOKS)}")
    print()

    success_count = 0
    fail_count = 0

    for i, (name, start, end) in enumerate(BOOKS, 1):
        print(f"[{i:2d}/{len(BOOKS)}] Extracting {name} (pages {start}-{end})...")
        if extract_book(name, start, end):
            success_count += 1
        else:
            fail_count += 1

    print()
    print("=" * 40)
    print(f"Complete: {success_count} books extracted, {fail_count} failed")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
