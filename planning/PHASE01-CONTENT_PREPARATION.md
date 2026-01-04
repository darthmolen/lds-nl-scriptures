# Phase 1: Content Preparation

## Objective

Convert raw PDF scripture content to structured markdown format suitable for parsing and ingestion.

## Input Files

### Scriptures (Priority 1)
| File | Language | Pages | Location |
|------|----------|-------|----------|
| lds_scriptures_quad_en.pdf | English | 3,839 | `content/raw/scriptures/` |
| lds_scriptures_quad_es.pdf | Spanish | TBD | `content/raw/escrituras/` |

### Come Follow Me (Phase 7)
Deferred to Phase 7 - see PHASE07-COME_FOLLOW_ME.md

## Conversion Tool

Using **pymupdf4llm** for CPU-friendly incremental extraction:

- **Library**: [pymupdf4llm](https://github.com/pymupdf/pymupdf4llm) - lightweight, no GPU required
- **Approach**: TOC-based incremental extraction by book
- **Advantage**: Works in Claude Code web environment

```python
import pymupdf4llm

# Extract specific page range (0-indexed)
md = pymupdf4llm.to_markdown("quad.pdf", pages=list(range(11, 89)))
```

## PDF Structure (English Quad)

The PDF contains embedded Table of Contents with 213 entries:

| Section | Start Page | End Page | Notes |
|---------|------------|----------|-------|
| Old Testament | 12 | 1195 | 39 books |
| New Testament | 1196 | 1605 | 27 books |
| **Topical Guide** | 1606 | 2187 | Bonus! Already in PDF |
| Bible Dictionary | 2188 | 2353 | Reference material |
| Book of Mormon | 2472 | 3021 | 15 books |
| Doctrine & Covenants | 3022 | 3329 | 138 sections |
| Pearl of Great Price | 3330 | 3405 | 5 books |

### Book-Level TOC (Sample)
```
Old Testament -> p.12
  Genesis -> p.12
  Exodus -> p.90
  Leviticus -> p.157
  ...
Book of Mormon -> p.2472
  1 Nephi -> p.2472
  2 Nephi -> p.2510
  ...
```

## Output Structure

```
content/
├── raw/                           # Source PDFs (existing)
│   ├── scriptures/
│   └── escrituras/
└── processed/                     # Converted markdown (new)
    └── scriptures/
        ├── en/
        │   ├── old-testament/
        │   │   ├── genesis.md
        │   │   ├── exodus.md
        │   │   └── ...
        │   ├── new-testament/
        │   │   ├── matthew.md
        │   │   └── ...
        │   ├── book-of-mormon/
        │   │   ├── 1-nephi.md
        │   │   └── ...
        │   ├── doctrine-and-covenants/
        │   │   └── dc.md
        │   ├── pearl-of-great-price/
        │   │   └── pgp.md
        │   └── topical-guide/
        │       └── topical-guide.md
        └── es/
            └── (same structure)
```

## Tasks

### 1.1 Environment Setup
- [ ] Verify pymupdf4llm is installed (`pip install pymupdf4llm`)
- [ ] Test extraction on a single chapter

### 1.2 Build Extraction Script
- [ ] Create `scripts/extract_scriptures.py`
- [ ] Parse TOC to build book → page range mapping
- [ ] Extract each book to separate markdown file
- [ ] Handle both EN and ES quads

### 1.3 Scripture Extraction (English)
Extract in order, committing after each standard work:

- [ ] Old Testament (39 books)
- [ ] New Testament (27 books)
- [ ] Book of Mormon (15 books)
- [ ] Doctrine & Covenants
- [ ] Pearl of Great Price
- [ ] Topical Guide (bonus)

### 1.4 Scripture Extraction (Spanish)
- [ ] Verify Spanish PDF has similar TOC structure
- [ ] Run same extraction process
- [ ] Validate output

### 1.5 Post-Processing Assessment
- [ ] Analyze markdown structure (headers, verses, chapters)
- [ ] Identify parsing patterns for verse extraction
- [ ] Document any conversion artifacts or issues
- [ ] Determine if cleanup scripts are needed

### 1.6 Quality Validation
- [ ] Spot-check verses across all standard works
- [ ] Verify chapter/verse numbering integrity
- [ ] Compare sample verses against official text

## Extraction Script Outline

```python
#!/usr/bin/env python3
"""Extract scriptures from PDF using TOC-based page ranges."""

import pymupdf
import pymupdf4llm
from pathlib import Path

def get_toc_mapping(pdf_path: str) -> dict:
    """Build book -> (start_page, end_page) mapping from TOC."""
    doc = pymupdf.open(pdf_path)
    toc = doc.get_toc()

    # Parse TOC entries to find book boundaries
    books = {}
    # ... implementation
    return books

def extract_book(pdf_path: str, book_name: str, start_page: int, end_page: int, output_dir: Path):
    """Extract a single book to markdown."""
    pages = list(range(start_page - 1, end_page))  # 0-indexed
    md = pymupdf4llm.to_markdown(pdf_path, pages=pages)

    output_file = output_dir / f"{book_name.lower().replace(' ', '-')}.md"
    output_file.write_text(md, encoding="utf-8")
    print(f"Extracted {book_name} -> {output_file}")

def main():
    pdf_path = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
    output_dir = Path("content/processed/scriptures/en")

    books = get_toc_mapping(pdf_path)
    for book_name, (start, end) in books.items():
        extract_book(pdf_path, book_name, start, end, output_dir)

if __name__ == "__main__":
    main()
```

## Expected Challenges

1. **Two-column layout**: Scripture pages use two columns; pymupdf4llm handles this reasonably well
2. **Verse numbering**: Need to verify verse numbers are preserved
3. **Footnotes/cross-references**: May appear inline or at page bottom
4. **Chapter headings**: Various formatting across standard works

## Success Criteria

- [ ] All books extracted to individual markdown files
- [ ] Both EN and ES quads processed
- [ ] Markdown preserves book/chapter/verse structure
- [ ] Content readable and parseable for Phase 2

## Dependencies

- Python 3.10+
- pymupdf (`pip install pymupdf`)
- pymupdf4llm (`pip install pymupdf4llm`)

## Notes

- No GPU required - runs on CPU
- Incremental extraction allows progress commits
- Topical Guide found in PDF - no separate source needed!
- Bible Dictionary also available if needed later
