# Phase 1A: Old Testament Extraction

## Overview
Extract Old Testament books from the quad PDF to markdown.

**Pages:** 12-1195 (1,184 pages)
**Books:** 39
**Output:** `content/processed/scriptures/en/old-testament/`

## Books to Extract

| # | Book | Start | End | Pages |
|---|------|-------|-----|-------|
| 1 | Genesis | 12 | 89 | 78 |
| 2 | Exodus | 90 | 156 | 67 |
| 3 | Leviticus | 157 | 200 | 44 |
| 4 | Numbers | 201 | 262 | 62 |
| 5 | Deuteronomy | 263 | 318 | 56 |
| 6 | Joshua | 319 | 353 | 35 |
| 7 | Judges | 354 | 387 | 34 |
| 8 | Ruth | 388 | 392 | 5 |
| 9 | 1 Samuel | 393 | 436 | 44 |
| 10 | 2 Samuel | 437 | 473 | 37 |
| 11 | 1 Kings | 474 | 517 | 44 |
| 12 | 2 Kings | 518 | 558 | 41 |
| 13 | 1 Chronicles | 559 | 597 | 39 |
| 14 | 2 Chronicles | 598 | 644 | 47 |
| 15 | Ezra | 645 | 658 | 14 |
| 16 | Nehemiah | 659 | 678 | 20 |
| 17 | Esther | 679 | 688 | 10 |
| 18 | Job | 689 | 724 | 36 |
| 19 | Psalms | 725 | 821 | 97 |
| 20 | Proverbs | 822 | 855 | 34 |
| 21 | Ecclesiastes | 856 | 866 | 11 |
| 22 | Song of Solomon | 867 | 871 | 5 |
| 23 | Isaiah | 872 | 952 | 81 |
| 24 | Jeremiah | 953 | 1030 | 78 |
| 25 | Lamentations | 1031 | 1037 | 7 |
| 26 | Ezekiel | 1038 | 1109 | 72 |
| 27 | Daniel | 1110 | 1132 | 23 |
| 28 | Hosea | 1133 | 1143 | 11 |
| 29 | Joel | 1144 | 1147 | 4 |
| 30 | Amos | 1148 | 1156 | 9 |
| 31 | Obadiah | 1157 | 1157 | 1 |
| 32 | Jonah | 1158 | 1160 | 3 |
| 33 | Micah | 1161 | 1166 | 6 |
| 34 | Nahum | 1167 | 1169 | 3 |
| 35 | Habakkuk | 1170 | 1172 | 3 |
| 36 | Zephaniah | 1173 | 1176 | 4 |
| 37 | Haggai | 1177 | 1178 | 2 |
| 38 | Zechariah | 1179 | 1190 | 12 |
| 39 | Malachi | 1191 | 1195 | 5 |

## Extraction Command

```python
import pymupdf4llm
from pathlib import Path

PDF_PATH = "content/raw/scriptures/lds_scriptures_quad_en.pdf"
OUTPUT_DIR = Path("content/processed/scriptures/en/old-testament")

BOOKS = [
    ("genesis", 12, 89),
    ("exodus", 90, 156),
    ("leviticus", 157, 200),
    ("numbers", 201, 262),
    ("deuteronomy", 263, 318),
    ("joshua", 319, 353),
    ("judges", 354, 387),
    ("ruth", 388, 392),
    ("1-samuel", 393, 436),
    ("2-samuel", 437, 473),
    ("1-kings", 474, 517),
    ("2-kings", 518, 558),
    ("1-chronicles", 559, 597),
    ("2-chronicles", 598, 644),
    ("ezra", 645, 658),
    ("nehemiah", 659, 678),
    ("esther", 679, 688),
    ("job", 689, 724),
    ("psalms", 725, 821),
    ("proverbs", 822, 855),
    ("ecclesiastes", 856, 866),
    ("song-of-solomon", 867, 871),
    ("isaiah", 872, 952),
    ("jeremiah", 953, 1030),
    ("lamentations", 1031, 1037),
    ("ezekiel", 1038, 1109),
    ("daniel", 1110, 1132),
    ("hosea", 1133, 1143),
    ("joel", 1144, 1147),
    ("amos", 1148, 1156),
    ("obadiah", 1157, 1157),
    ("jonah", 1158, 1160),
    ("micah", 1161, 1166),
    ("nahum", 1167, 1169),
    ("habakkuk", 1170, 1172),
    ("zephaniah", 1173, 1176),
    ("haggai", 1177, 1178),
    ("zechariah", 1179, 1190),
    ("malachi", 1191, 1195),
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, start, end in BOOKS:
    pages = list(range(start - 1, end))  # 0-indexed
    md = pymupdf4llm.to_markdown(PDF_PATH, pages=pages)
    (OUTPUT_DIR / f"{name}.md").write_text(md, encoding="utf-8")
    print(f"✓ {name}")
```

## Validation Checklist

- [ ] All 39 books extracted
- [ ] Spot check Genesis 1:1
- [ ] Spot check Psalms 23
- [ ] Spot check Isaiah 53
- [ ] Verify chapter/verse numbers visible
- [ ] Check for two-column artifacts
