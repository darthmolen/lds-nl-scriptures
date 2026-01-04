# Phase 1C: Book of Mormon Extraction

## Overview
Extract Book of Mormon books from the quad PDF to markdown.

**Pages:** 2472-3015 (544 pages)
**Books:** 15
**Output:** `content/processed/scriptures/en/book-of-mormon/`

## Books to Extract

| # | Book | Start | End | Pages |
|---|------|-------|-----|-------|
| 1 | 1 Nephi | 2484 | 2535 | 52 |
| 2 | 2 Nephi | 2536 | 2599 | 64 |
| 3 | Jacob | 2600 | 2618 | 19 |
| 4 | Enos | 2619 | 2620 | 2 |
| 5 | Jarom | 2621 | 2622 | 2 |
| 6 | Omni | 2623 | 2625 | 3 |
| 7 | Words of Mormon | 2626 | 2627 | 2 |
| 8 | Mosiah | 2628 | 2689 | 62 |
| 9 | Alma | 2690 | 2850 | 161 |
| 10 | Helaman | 2851 | 2888 | 38 |
| 11 | 3 Nephi | 2889 | 2947 | 59 |
| 12 | 4 Nephi | 2948 | 2951 | 4 |
| 13 | Mormon | 2952 | 2969 | 18 |
| 14 | Ether | 2970 | 3000 | 31 |
| 15 | Moroni | 3001 | 3015 | 15 |

**Note:** Title page and introduction are on pages 2472-2483.

## Extraction Command

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/book-of-mormon")

BOOKS = [
    ("1-nephi", 2484, 2535),
    ("2-nephi", 2536, 2599),
    ("jacob", 2600, 2618),
    ("enos", 2619, 2620),
    ("jarom", 2621, 2622),
    ("omni", 2623, 2625),
    ("words-of-mormon", 2626, 2627),
    ("mosiah", 2628, 2689),
    ("alma", 2690, 2850),
    ("helaman", 2851, 2888),
    ("3-nephi", 2889, 2947),
    ("4-nephi", 2948, 2951),
    ("mormon", 2952, 2969),
    ("ether", 2970, 3000),
    ("moroni", 3001, 3015),
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, start, end in BOOKS:
    pages = list(range(start - 1, end))  # 0-indexed
    md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
    (OUTPUT_DIR / f"{name}.md").write_text(md, encoding="utf-8")
    print(f"✓ {name}")
```

## Validation Checklist

- [ ] All 15 books extracted
- [ ] Spot check 1 Nephi 3:7
- [ ] Spot check Mosiah 3:19
- [ ] Spot check Alma 32 (faith chapter)
- [ ] Spot check Moroni 10:4-5
- [ ] Verify chapter/verse numbers visible
- [ ] Check for two-column artifacts
