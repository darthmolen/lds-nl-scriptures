#!/usr/bin/env python3
"""Extract Genesis from the quad PDF using pdftext (simpler extraction)."""

from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PDF_PATH = PROJECT_ROOT / "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = PROJECT_ROOT / "content/processed/scriptures/en/old-testament"

# Genesis: pages 12-89 (1-indexed in the doc)
START_PAGE = 11  # 0-indexed (page 12)
END_PAGE = 88    # 0-indexed inclusive (page 89)

def main():
    from pdftext.extraction import plain_text_output

    print(f"Extracting Genesis (pages 12-89) from {PDF_PATH}...")

    # pdftext uses page_range parameter
    page_range = list(range(START_PAGE, END_PAGE + 1))

    # Extract text from specific pages
    text = plain_text_output(str(PDF_PATH), page_range=page_range)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save as markdown (plain text for now)
    output_path = OUTPUT_DIR / "genesis.md"
    output_path.write_text(text, encoding="utf-8")

    print(f"✓ Saved to {output_path}")
    print(f"  - Text length: {len(text):,} characters")

    # Print first 1000 chars as preview
    print("\n--- Preview (first 1000 chars) ---")
    print(text[:1000])
    print("...")

if __name__ == "__main__":
    main()
