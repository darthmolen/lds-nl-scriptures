# Phase 1B: New Testament Extraction

## Overview
Extract New Testament books from the quad PDF to markdown.

**Pages:** 1196-1605 (410 pages)
**Books:** 27
**Output:** `content/processed/scriptures/en/new-testament/`

## Books to Extract

| # | Book | Start | End | Pages |
|---|------|-------|-----|-------|
| 1 | Matthew | 1198 | 1251 | 54 |
| 2 | Mark | 1252 | 1281 | 30 |
| 3 | Luke | 1282 | 1334 | 53 |
| 4 | John | 1335 | 1375 | 41 |
| 5 | Acts | 1376 | 1425 | 50 |
| 6 | Romans | 1426 | 1448 | 23 |
| 7 | 1 Corinthians | 1449 | 1470 | 22 |
| 8 | 2 Corinthians | 1471 | 1483 | 13 |
| 9 | Galatians | 1484 | 1490 | 7 |
| 10 | Ephesians | 1491 | 1498 | 8 |
| 11 | Philippians | 1499 | 1503 | 5 |
| 12 | Colossians | 1504 | 1508 | 5 |
| 13 | 1 Thessalonians | 1509 | 1513 | 5 |
| 14 | 2 Thessalonians | 1514 | 1516 | 3 |
| 15 | 1 Timothy | 1517 | 1522 | 6 |
| 16 | 2 Timothy | 1523 | 1527 | 5 |
| 17 | Titus | 1528 | 1530 | 3 |
| 18 | Philemon | 1531 | 1531 | 1 |
| 19 | Hebrews | 1532 | 1548 | 17 |
| 20 | James | 1549 | 1554 | 6 |
| 21 | 1 Peter | 1555 | 1561 | 7 |
| 22 | 2 Peter | 1562 | 1565 | 4 |
| 23 | 1 John | 1566 | 1571 | 6 |
| 24 | 2 John | 1572 | 1572 | 1 |
| 25 | 3 John | 1573 | 1573 | 1 |
| 26 | Jude | 1574 | 1575 | 2 |
| 27 | Revelation | 1576 | 1605 | 30 |

## Extraction Command

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/new-testament")

BOOKS = [
    ("matthew", 1198, 1251),
    ("mark", 1252, 1281),
    ("luke", 1282, 1334),
    ("john", 1335, 1375),
    ("acts", 1376, 1425),
    ("romans", 1426, 1448),
    ("1-corinthians", 1449, 1470),
    ("2-corinthians", 1471, 1483),
    ("galatians", 1484, 1490),
    ("ephesians", 1491, 1498),
    ("philippians", 1499, 1503),
    ("colossians", 1504, 1508),
    ("1-thessalonians", 1509, 1513),
    ("2-thessalonians", 1514, 1516),
    ("1-timothy", 1517, 1522),
    ("2-timothy", 1523, 1527),
    ("titus", 1528, 1530),
    ("philemon", 1531, 1531),
    ("hebrews", 1532, 1548),
    ("james", 1549, 1554),
    ("1-peter", 1555, 1561),
    ("2-peter", 1562, 1565),
    ("1-john", 1566, 1571),
    ("2-john", 1572, 1572),
    ("3-john", 1573, 1573),
    ("jude", 1574, 1575),
    ("revelation", 1576, 1605),
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, start, end in BOOKS:
    pages = list(range(start - 1, end))  # 0-indexed
    md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
    (OUTPUT_DIR / f"{name}.md").write_text(md, encoding="utf-8")
    print(f"✓ {name}")
```

## Validation Checklist

- [ ] All 27 books extracted
- [ ] Spot check Matthew 5:1-12 (Beatitudes)
- [ ] Spot check John 3:16
- [ ] Spot check 1 Corinthians 13
- [ ] Verify chapter/verse numbers visible
- [ ] Check for two-column artifacts
