# Phase 1F: Topical Guide Extraction

## Overview
Extract Topical Guide from the quad PDF to markdown.

**Pages:** 1606-2187 (582 pages)
**Output:** `content/processed/scriptures/en/topical-guide/`

## Structure

The Topical Guide is organized alphabetically A-Z with topics and scripture references.

| Letter | Start | End | Pages |
|--------|-------|-----|-------|
| A | 1606 | 1624 | 19 |
| B | 1625 | 1652 | 28 |
| C | 1653 | 1687 | 35 |
| D | 1688 | 1716 | 29 |
| E | 1717 | 1734 | 18 |
| F | 1735 | 1763 | 29 |
| G | 1764 | 1796 | 33 |
| H | 1797 | 1823 | 27 |
| I | 1824 | 1839 | 16 |
| J | 1840 | 1864 | 25 |
| K | 1865 | 1872 | 8 |
| L | 1873 | 1899 | 27 |
| M | 1900 | 1930 | 31 |
| N | 1931 | 1938 | 8 |
| O | 1939 | 1950 | 12 |
| P | 1951 | 1996 | 46 |
| Q | 1997 | 1997 | 1 |
| R | 1998 | 2031 | 34 |
| S | 2032 | 2102 | 71 |
| T | 2103 | 2132 | 30 |
| U | 2133 | 2140 | 8 |
| V | 2141 | 2148 | 8 |
| W | 2149 | 2182 | 34 |
| Y | 2183 | 2183 | 1 |
| Z | 2184 | 2187 | 4 |

## Extraction Options

### Option A: Single File
Extract entire Topical Guide as one markdown file.

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/topical-guide")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Extract entire Topical Guide
pages = list(range(1606 - 1, 2187))  # 0-indexed
md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
(OUTPUT_DIR / "topical-guide.md").write_text(md, encoding="utf-8")
print("✓ topical-guide")
```

### Option B: By Letter
Extract each letter section separately for easier processing.

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/topical-guide")

LETTERS = [
    ("a", 1606, 1624),
    ("b", 1625, 1652),
    ("c", 1653, 1687),
    ("d", 1688, 1716),
    ("e", 1717, 1734),
    ("f", 1735, 1763),
    ("g", 1764, 1796),
    ("h", 1797, 1823),
    ("i", 1824, 1839),
    ("j", 1840, 1864),
    ("k", 1865, 1872),
    ("l", 1873, 1899),
    ("m", 1900, 1930),
    ("n", 1931, 1938),
    ("o", 1939, 1950),
    ("p", 1951, 1996),
    ("q", 1997, 1997),
    ("r", 1998, 2031),
    ("s", 2032, 2102),
    ("t", 2103, 2132),
    ("u", 2133, 2140),
    ("v", 2141, 2148),
    ("w", 2149, 2182),
    ("y", 2183, 2183),
    ("z", 2184, 2187),
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, start, end in LETTERS:
    pages = list(range(start - 1, end))  # 0-indexed
    md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
    (OUTPUT_DIR / f"tg-{name}.md").write_text(md, encoding="utf-8")
    print(f"✓ {name}")
```

## Special Considerations

The Topical Guide has a unique structure:
- **Topics** are bold headings
- **Subtopics** are indented under main topics
- **Scripture references** follow each topic/subtopic
- **Cross-references** link to related topics ("See also...")

### Example Structure
```
ATONEMENT
    See also Jesus Christ, Atonement through; Redemption
    Lev. 16:10 scapegoat...let him go for a...
    Mosiah 3:11 his blood atoneth for the sins of...
```

## Validation Checklist

- [ ] All letters A-Z extracted
- [ ] Spot check "Atonement" topic
- [ ] Spot check "Faith" topic
- [ ] Spot check "Jesus Christ" entries
- [ ] Verify cross-references preserved
- [ ] Check scripture citations readable

## Phase 2 Note

The Topical Guide will require special parsing in Phase 2 to extract:
1. Topic names
2. Subtopic relationships
3. Scripture references (book, chapter, verse)
4. Cross-reference links

This will populate the `topical_guide` database table.
