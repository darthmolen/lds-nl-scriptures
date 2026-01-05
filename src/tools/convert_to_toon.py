#!/usr/bin/env python3
"""Convert JSON scripture and CFM data to TOON format.

TOON (Token-Oriented Object Notation) reduces LLM token usage by 30-60%
compared to JSON, especially for uniform tabular data like scriptures.

Usage:
    python convert_to_toon.py --type scriptures
    python convert_to_toon.py --type cfm
    python convert_to_toon.py --type all
"""

import json
import toons
import tiktoken
from pathlib import Path
from typing import Any

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_DIR = PROJECT_ROOT / "content" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "content" / "transformed"

# Token encoder for metrics
ENCODER = tiktoken.get_encoding("cl100k_base")  # GPT-4/Claude tokenizer


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken."""
    return len(ENCODER.encode(text))


def flatten_scriptures_for_toon(data: dict) -> list[dict]:
    """Flatten nested scripture JSON into flat verse records for optimal TOON encoding.

    Handles two structures:
    1. Individual volume file: {"title": "...", "books": {...}} - no vol column
    2. Combined file: {"volumeid": {"title": "...", "books": {...}}} - includes vol column

    Output: flat list of verse records (ideal for TOON tabular format)
    """
    verses = []

    # Detect structure: individual volume vs combined
    is_individual = "books" in data
    if is_individual:
        # Individual volume file - wrap for processing but don't include vol in output
        volumes = {"_single": data}
    else:
        # Combined file or multiple volumes - include vol column
        volumes = data

    for volume_id, volume in volumes.items():
        if isinstance(volume, str):
            continue  # Skip non-dict entries like "title"

        for book_id, book in volume.get("books", {}).items():
            book_title = book.get("title", book_id)

            for chapter_num, chapter in book.get("chapters", {}).items():
                for verse_idx, verse in enumerate(chapter.get("verses", []), 1):
                    # Flatten footnotes to compact string format
                    footnotes_compact = []
                    for fn in verse.get("footnotes", []) or verse.get("footnote_markers", []):
                        if "footnote" in fn:
                            # English format: {footnote, start, end}
                            footnotes_compact.append(
                                f"{fn.get('start', '')}:{fn.get('end', '')}:{fn['footnote']}"
                            )
                        elif "marker" in fn:
                            # Spanish format: {marker, note_id, footnote}
                            footnotes_compact.append(
                                f"{fn.get('marker', '')}:{fn.get('footnote', '')}"
                            )

                    verse_record = {
                        "book": book_id,
                        "ch": int(chapter_num),
                        "vs": verse_idx,
                        "text": verse.get("text", ""),
                        "fn": "|".join(footnotes_compact) if footnotes_compact else ""
                    }

                    # Only include vol column for combined files
                    if not is_individual:
                        verse_record = {"vol": volume_id, **verse_record}

                    verses.append(verse_record)

    return verses


def flatten_cfm_for_toon(data: dict) -> list[dict]:
    """Flatten CFM lesson data for optimal TOON encoding."""
    lessons = []

    for lesson_id, lesson in data.get("lessons", {}).items():
        # Flatten sections into single text
        sections_text = []
        for section in lesson.get("sections", []):
            if section.get("title"):
                sections_text.append(f"## {section['title']}")
            sections_text.extend(section.get("paragraphs", []))

        lessons.append({
            "id": lesson_id,
            "title": lesson.get("title", ""),
            "date": lesson.get("date_range", ""),
            "refs": ",".join(lesson.get("scripture_refs", [])[:10]),
            "text": "\n".join(sections_text) if sections_text else lesson.get("plain_text", "")[:5000]
        })

    return lessons


def convert_file(input_path: Path, output_path: Path, flatten_func) -> dict:
    """Convert a single JSON file to TOON format."""
    # Read JSON
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Flatten for optimal TOON encoding
    flat_data = flatten_func(data)

    # Get JSON string for comparison
    json_str = json.dumps(flat_data, ensure_ascii=False)
    json_tokens = count_tokens(json_str)

    # Convert to TOON
    toon_str = toons.dumps(flat_data)
    toon_tokens = count_tokens(toon_str)

    # Save TOON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(toon_str)

    # Calculate savings
    savings_pct = (1 - toon_tokens / json_tokens) * 100 if json_tokens > 0 else 0

    return {
        "input": str(input_path),
        "output": str(output_path),
        "records": len(flat_data),
        "json_size": len(json_str),
        "toon_size": len(toon_str),
        "json_tokens": json_tokens,
        "toon_tokens": toon_tokens,
        "savings_pct": savings_pct
    }


def convert_scriptures():
    """Convert all scripture JSON files to TOON."""
    print("=" * 60)
    print("CONVERTING SCRIPTURES TO TOON")
    print("=" * 60)

    results = []

    for lang in ["en", "es"]:
        input_dir = INPUT_DIR / "scriptures" / lang
        output_dir = OUTPUT_DIR / "scriptures" / lang

        # Process each volume separately (not all_scriptures.json - too big)
        for json_file in sorted(input_dir.glob("*.json")):
            if json_file.name == "all_scriptures.json":
                continue  # Skip combined file

            output_file = output_dir / json_file.name.replace(".json", ".toon")

            print(f"  {json_file.name}...", end=" ", flush=True)

            result = convert_file(json_file, output_file, flatten_scriptures_for_toon)
            results.append(result)

            print(f"{result['records']} verses, {result['savings_pct']:.1f}% savings")

    return results


def convert_cfm():
    """Convert all CFM JSON files to TOON."""
    print("\n" + "=" * 60)
    print("CONVERTING COME FOLLOW ME TO TOON")
    print("=" * 60)

    results = []

    for lang in ["en", "es"]:
        input_dir = INPUT_DIR / "cfm" / lang
        output_dir = OUTPUT_DIR / "cfm" / lang

        for json_file in sorted(input_dir.glob("*.json")):
            output_file = output_dir / json_file.name.replace(".json", ".toon")

            print(f"  {json_file.name}...", end=" ", flush=True)

            result = convert_file(json_file, output_file, flatten_cfm_for_toon)
            results.append(result)

            print(f"{result['records']} lessons, {result['savings_pct']:.1f}% savings")

    return results


def print_summary(results: list[dict]):
    """Print summary of conversion results."""
    total_json_tokens = sum(r["json_tokens"] for r in results)
    total_toon_tokens = sum(r["toon_tokens"] for r in results)
    total_json_size = sum(r["json_size"] for r in results)
    total_toon_size = sum(r["toon_size"] for r in results)

    overall_savings = (1 - total_toon_tokens / total_json_tokens) * 100 if total_json_tokens > 0 else 0
    size_savings = (1 - total_toon_size / total_json_size) * 100 if total_json_size > 0 else 0

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files converted: {len(results)}")
    print(f"JSON tokens:     {total_json_tokens:,}")
    print(f"TOON tokens:     {total_toon_tokens:,}")
    print(f"Token savings:   {overall_savings:.1f}%")
    print(f"Size savings:    {size_savings:.1f}% ({total_json_size:,} -> {total_toon_size:,} bytes)")
    print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert JSON to TOON format")
    parser.add_argument("--type", choices=["scriptures", "cfm", "all"], default="all",
                        help="What to convert (default: all)")
    args = parser.parse_args()

    results = []

    if args.type in ["scriptures", "all"]:
        results.extend(convert_scriptures())

    if args.type in ["cfm", "all"]:
        results.extend(convert_cfm())

    print_summary(results)

    print(f"\nOutput saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
