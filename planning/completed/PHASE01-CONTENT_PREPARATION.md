# Phase 1: Content Preparation (Completed)

**Status:** Completed January 4, 2026

## Objective

Extract structured scripture content and Come Follow Me lessons for LLM-based search and retrieval.

## Approach Pivot

**Original plan:** PDF extraction using pymupdf4llm or Marker.

**What happened:** Both PDF tools struggled with dual-column scripture layouts and footnote mixing. Discovered APIs that provide structured data directly:

- **Open Scripture API** - English scriptures with footnotes and character positions
- **Church of Jesus Christ API** - Spanish scriptures and Come Follow Me lessons

This eliminated the need for PDF extraction entirely for scriptures.

## Data Sources

| Content | Source | API |
|---------|--------|-----|
| English Scriptures | Open Scripture API | `openscriptureapi.org/api/scriptures/v1/lds/en/` |
| Spanish Scriptures | Church API | `churchofjesuschrist.org/study/api/v3/language-pages/type/content` |
| Come Follow Me (EN/ES) | Church API | Same as Spanish scriptures |

## Implementation

### Scripts Created

| Script | Purpose |
|--------|---------|
| [fetch_scriptures.py](../../src/tools/fetch_scriptures.py) | Fetch all scriptures from APIs |
| [fetch_cfm.py](../../src/tools/fetch_cfm.py) | Fetch Come Follow Me lessons |
| [convert_to_toon.py](../../src/tools/convert_to_toon.py) | Convert JSON to TOON format |

### Data Fetched

**Scriptures:**

| Volume | English Verses | Spanish Verses |
|--------|----------------|----------------|
| Old Testament | 23,145 | 23,145 |
| New Testament | 7,957 | 7,958 |
| Book of Mormon | 6,604 | 6,604 |
| Doctrine & Covenants | 3,654 | 3,654 |
| Pearl of Great Price | 635 | 635 |
| **Total** | **41,995** | **41,996** |

**Come Follow Me:**

| Year | Scripture | EN Lessons | ES Lessons |
|------|-----------|------------|------------|
| 2026 | Old Testament | 52 | 52 |
| 2025 | D&C | 52 | 52 |
| 2024 | Book of Mormon | 52 | 52 |
| 2023 | New Testament | 52 | 52 |

## Output Structure

```text
content/
├── processed/              # Source JSON from APIs
│   ├── scriptures/
│   │   ├── en/
│   │   │   ├── oldtestament.json
│   │   │   ├── newtestament.json
│   │   │   ├── bookofmormon.json
│   │   │   ├── doctrineandcovenants.json
│   │   │   ├── pearlofgreatprice.json
│   │   │   └── all_scriptures.json
│   │   └── es/
│   │       └── (same structure)
│   └── cfm/
│       ├── en/
│       │   ├── cfm_ot_2026.json
│       │   ├── cfm_dc_2025.json
│       │   ├── cfm_bom_2024.json
│       │   └── cfm_nt_2023.json
│       └── es/
│           └── (same structure)
└── transformed/            # TOON format for Claude Projects
    ├── scriptures/{en,es}/*.toon
    └── cfm/{en,es}/*.toon
```

## TOON Conversion Results

Converted to TOON format for 23.6% token reduction (optimized for Claude Projects):

| Content | JSON Tokens | TOON Tokens | Savings |
|---------|-------------|-------------|---------|
| Scriptures | 6.7M | 5.1M | 23.6% |
| CFM | ~3.5M | ~3.5M | 0.5% |

See [TOON-FORMAT-SUMMARY.md](../../documentation/TOON-FORMAT-SUMMARY.md) for format details.

## Data Quality

**English scriptures include:**

- Full verse text
- Footnotes with character positions (`start`, `end`)
- Chapter summaries
- Cross-references (TG, BD, etc.)

**Spanish scriptures include:**

- Full verse text
- Footnote markers with references
- Chapter summaries

**CFM lessons include:**

- Lesson title and date range
- Scripture references
- Section content (paragraphs)
- Full plain text

## What Was NOT Implemented

The original plan called for PDF extraction with sub-phases (1A-1F) for each standard work. These were replaced by API-based extraction:

- PHASE1A-OT.md - Old Testament PDF extraction
- PHASE1B-NT.md - New Testament PDF extraction
- PHASE1C-BOM.md - Book of Mormon PDF extraction
- PHASE1D-DC.md - D&C PDF extraction
- PHASE1E-PGP.md - Pearl of Great Price PDF extraction
- PHASE1F-TG.md - Topical Guide PDF extraction

**Note:** Topical Guide extraction was not done. The TG is embedded in the quad PDF and would still require PDF extraction if needed later.

## Success Criteria

- [x] All English standard works extracted (41,995 verses)
- [x] All Spanish standard works extracted (41,996 verses)
- [x] Come Follow Me lessons extracted (4 years x 2 languages)
- [x] Data includes footnotes and cross-references
- [x] Content converted to token-efficient TOON format
- [x] Ready for Phase 2 database ingestion
