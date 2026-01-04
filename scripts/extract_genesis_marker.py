#!/usr/bin/env python3
"""Extract Genesis from the quad PDF using marker (requires model downloads).

Run locally where you have:
- Access to download models from models.datalab.to
- Optionally a GPU for faster processing (works on CPU too, just slower)

Usage:
    python scripts/extract_genesis_marker.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PDF_PATH = PROJECT_ROOT / "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = PROJECT_ROOT / "content/processed/scriptures/en/old-testament"

# Genesis: pages 12-89 (1-indexed in the doc, marker uses 0-indexed)
START_PAGE = 11  # 0-indexed (page 12)
END_PAGE = 88    # 0-indexed inclusive (page 89)


def main():
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    print("Loading marker models (first run downloads ~2GB of models)...")
    converter = PdfConverter(artifact_dict=create_model_dict())

    print(f"Extracting Genesis (pages 12-89) from {PDF_PATH}...")
    print("This may take several minutes on CPU...")

    # marker uses page_range as a list of page numbers (0-indexed)
    page_range = list(range(START_PAGE, END_PAGE + 1))

    rendered = converter(str(PDF_PATH), page_range=page_range)
    text, metadata, images = text_from_rendered(rendered)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save markdown
    output_path = OUTPUT_DIR / "genesis_marker.md"
    output_path.write_text(text, encoding="utf-8")

    print(f"\n✓ Saved to {output_path}")
    print(f"  - Markdown length: {len(text):,} characters")
    print(f"  - Images extracted: {len(images) if images else 0}")

    # Save images if any
    if images:
        images_dir = OUTPUT_DIR / "genesis_images"
        images_dir.mkdir(exist_ok=True)
        for img_name, img_data in images.items():
            img_path = images_dir / img_name
            if isinstance(img_data, bytes):
                img_path.write_bytes(img_data)
            else:
                img_data.save(str(img_path))
        print(f"  - Images saved to: {images_dir}")

    # Print preview
    print("\n--- Preview (first 2000 chars) ---")
    print(text[:2000])
    print("\n...")

    # Print metadata
    print("\n--- Metadata ---")
    for key, value in (metadata or {}).items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
