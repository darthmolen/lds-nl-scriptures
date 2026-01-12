#!/usr/bin/env python3
"""Convert conference JSON to TOON format.

TOON (Token-Oriented Object Notation) provides 30-60% token savings
for tabular data compared to JSON.

Usage:
    # Single conference:
    python -m src.transform.conference_to_toon --year 2024 --month 10 --lang en

    # All conferences:
    python -m src.transform.conference_to_toon --all --lang en

Input: content/processed/conference/{lang}/{year}_{month}.json
Output: content/transformed/conference/{lang}/{year}_{month}.toon
"""

import argparse
import json
from pathlib import Path

import toons


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert conference JSON to TOON format"
    )
    parser.add_argument("--year", type=int, help="Conference year")
    parser.add_argument("--month", choices=["04", "10"], help="Conference month")
    parser.add_argument("--all", action="store_true", help="Convert all conferences")
    parser.add_argument("--lang", choices=["en", "es"], required=True)
    return parser


def convert_conference(input_file: Path, output_file: Path) -> tuple[int, int]:
    """Convert a single conference JSON to TOON.

    Returns (json_size, toon_size) for comparison.
    """
    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    # Flatten into tabular format for maximum TOON efficiency
    # Each row: year, month, talk_uri, speaker, para_num, text
    rows = []
    for talk in data["talks"]:
        for para in talk["paragraphs"]:
            rows.append({
                "year": data["year"],
                "month": data["month"],
                "uri": talk["uri"],
                "speaker": talk["speaker_name"] or "",
                "num": para["num"],
                "text": para["text"],
            })

    # Create TOON-optimized structure
    toon_data = {
        "meta": {
            "year": data["year"],
            "month": data["month"],
            "lang": data["lang"],
            "talks": data["talk_count"],
            "paragraphs": data["paragraph_count"],
        },
        "paragraphs": rows,
    }

    # Convert to TOON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    toon_str = toons.dumps(toon_data)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(toon_str)

    json_size = input_file.stat().st_size
    toon_size = output_file.stat().st_size

    return json_size, toon_size


def get_available_json_files(input_dir: Path) -> list[Path]:
    """Get list of available JSON files."""
    if not input_dir.exists():
        return []
    return sorted(input_dir.glob("*.json"))


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    input_dir = Path(f"content/processed/conference/{args.lang}")
    output_dir = Path(f"content/transformed/conference/{args.lang}")

    if args.all:
        json_files = get_available_json_files(input_dir)
        if not json_files:
            print(f"No JSON files found in {input_dir}")
            return
    elif args.year and args.month:
        json_files = [input_dir / f"{args.year}_{args.month}.json"]
        if not json_files[0].exists():
            print(f"File not found: {json_files[0]}")
            return
    else:
        parser.error("Must specify either --all or both --year and --month")
        return

    print(f"Converting {len(json_files)} conferences to TOON...")

    total_json = 0
    total_toon = 0

    for json_file in json_files:
        output_file = output_dir / json_file.name.replace(".json", ".toon")

        json_size, toon_size = convert_conference(json_file, output_file)
        savings = (1 - toon_size / json_size) * 100 if json_size > 0 else 0

        print(f"  {json_file.name}: {json_size:,} -> {toon_size:,} bytes ({savings:.1f}% savings)")

        total_json += json_size
        total_toon += toon_size

    if total_json > 0:
        total_savings = (1 - total_toon / total_json) * 100
        print(f"\nTotal: {total_json:,} -> {total_toon:,} bytes ({total_savings:.1f}% savings)")


if __name__ == "__main__":
    main()
