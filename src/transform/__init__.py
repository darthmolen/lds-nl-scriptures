"""Transform module for Scripture Search project.

Provides utilities and scripts for converting processed JSON to TOON format
for token-efficient uploads to Claude Projects.

TOON (Token-Oriented Object Notation) provides 30-60% token savings
for tabular data compared to JSON.

Submodules:
- conference_to_toon: Convert conference JSON exports to TOON format

Usage:
    # Single conference:
    python -m src.transform.conference_to_toon --year 2024 --month 10 --lang en

    # All conferences:
    python -m src.transform.conference_to_toon --all --lang en
"""

__all__: list[str] = []
