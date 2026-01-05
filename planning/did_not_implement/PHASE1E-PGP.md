# Phase 1E: Pearl of Great Price Extraction

## Overview
Extract Pearl of Great Price books from the quad PDF to markdown.

**Pages:** 3330-3405 (76 pages)
**Books:** 5
**Output:** `content/processed/scriptures/en/pearl-of-great-price/`

## Books to Extract

| # | Book | Start | End | Pages |
|---|------|-------|-----|-------|
| 1 | Moses | 3336 | 3363 | 28 |
| 2 | Abraham | 3364 | 3377 | 14 |
| 3 | Joseph Smith—Matthew | 3378 | 3381 | 4 |
| 4 | Joseph Smith—History | 3382 | 3394 | 13 |
| 5 | Articles of Faith | 3395 | 3405 | 11 |

**Note:** Title page and introduction on pages 3330-3335.

## Extraction Command

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/pearl-of-great-price")

BOOKS = [
    ("moses", 3336, 3363),
    ("abraham", 3364, 3377),
    ("joseph-smith-matthew", 3378, 3381),
    ("joseph-smith-history", 3382, 3394),
    ("articles-of-faith", 3395, 3405),
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, start, end in BOOKS:
    pages = list(range(start - 1, end))  # 0-indexed
    md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
    (OUTPUT_DIR / f"{name}.md").write_text(md, encoding="utf-8")
    print(f"✓ {name}")
```

## Validation Checklist

- [ ] All 5 books extracted
- [ ] Spot check Moses 1:39
- [ ] Spot check Abraham 3:22-23
- [ ] Spot check JS-H 1:17-19 (First Vision)
- [ ] Verify Articles of Faith 1-13 complete
- [ ] Check for facsimile images in Abraham
