# Phase 1D: Doctrine & Covenants Extraction

## Overview
Extract Doctrine and Covenants from the quad PDF to markdown.

**Pages:** 3022-3329 (308 pages)
**Sections:** 138 + 2 Official Declarations
**Output:** `content/processed/scriptures/en/doctrine-and-covenants/`

## Structure

The D&C is organized by sections. The TOC groups them:
- Sections 1-24 (pages 3032-3074)
- Sections 25-49 (pages 3075-3121)
- Sections 50-74 (pages 3122-3164)
- Sections 75-99 (pages 3165-3223)
- Sections 100-124 (pages 3224-3286)
- Sections 125-138 (pages 3287-3321)
- Official Declaration 1 (pages 3322-3324)
- Official Declaration 2 (pages 3325-3329)

**Note:** Introduction and explanatory material on pages 3022-3031.

## Extraction Options

### Option A: Single File
Extract all of D&C as one markdown file.

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/doctrine-and-covenants")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Extract entire D&C
pages = list(range(3022 - 1, 3329))  # 0-indexed
md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
(OUTPUT_DIR / "doctrine-and-covenants.md").write_text(md, encoding="utf-8")
print("✓ doctrine-and-covenants")
```

### Option B: By Section Groups
Extract in chunks matching TOC structure.

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/doctrine-and-covenants")

SECTIONS = [
    ("sections-001-024", 3032, 3074),
    ("sections-025-049", 3075, 3121),
    ("sections-050-074", 3122, 3164),
    ("sections-075-099", 3165, 3223),
    ("sections-100-124", 3224, 3286),
    ("sections-125-138", 3287, 3321),
    ("official-declaration-1", 3322, 3324),
    ("official-declaration-2", 3325, 3329),
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, start, end in SECTIONS:
    pages = list(range(start - 1, end))  # 0-indexed
    md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
    (OUTPUT_DIR / f"{name}.md").write_text(md, encoding="utf-8")
    print(f"✓ {name}")
```

## Validation Checklist

- [ ] All sections extracted (1-138 + 2 ODs)
- [ ] Spot check D&C 1:37-39
- [ ] Spot check D&C 76 (vision of kingdoms)
- [ ] Spot check D&C 121:34-46
- [ ] Verify section headers visible
- [ ] Check Official Declarations included
