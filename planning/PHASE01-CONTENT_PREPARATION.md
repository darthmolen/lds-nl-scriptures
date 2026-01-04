# Phase 1: Content Preparation

## Objective

Convert raw PDF scripture content to structured markdown format suitable for parsing and ingestion.

## Tool

Using **pymupdf4llm** for CPU-friendly incremental extraction:

```bash
pip install pymupdf pymupdf4llm
```

```python
import pymupdf4llm

# Extract specific page range (0-indexed)
md = pymupdf4llm.to_markdown("quad.pdf", pages=list(range(11, 89)))
```

## Sub-Phases

| Phase | Standard Work | Pages | Books | Details |
|-------|--------------|-------|-------|---------|
| [1A](./PHASE1A-OT.md) | Old Testament | 12-1195 | 39 | Genesis → Malachi |
| [1B](./PHASE1B-NT.md) | New Testament | 1196-1605 | 27 | Matthew → Revelation |
| [1C](./PHASE1C-BOM.md) | Book of Mormon | 2472-3015 | 15 | 1 Nephi → Moroni |
| [1D](./PHASE1D-DC.md) | Doctrine & Covenants | 3022-3329 | 138+2 | Sections + ODs |
| [1E](./PHASE1E-PGP.md) | Pearl of Great Price | 3330-3405 | 5 | Moses → Articles of Faith |
| [1F](./PHASE1F-TG.md) | Topical Guide | 1606-2187 | A-Z | Topic → Scripture refs |

## Input Files

| File | Language | Pages | Location |
|------|----------|-------|----------|
| lds_scriptures_quad_en.pdf | English | 3,839 | `content/raw/scriptures/` |
| lds_scriptures_quad_es.pdf | Spanish | TBD | `content/raw/escrituras/` |

## Output Structure

```
content/processed/scriptures/
├── en/
│   ├── old-testament/
│   │   ├── genesis.md
│   │   ├── exodus.md
│   │   └── ... (39 books)
│   ├── new-testament/
│   │   ├── matthew.md
│   │   └── ... (27 books)
│   ├── book-of-mormon/
│   │   ├── 1-nephi.md
│   │   └── ... (15 books)
│   ├── doctrine-and-covenants/
│   │   └── doctrine-and-covenants.md
│   ├── pearl-of-great-price/
│   │   ├── moses.md
│   │   └── ... (5 books)
│   └── topical-guide/
│       └── topical-guide.md
└── es/
    └── (same structure)
```

## Execution Order

1. **Phase 1A** - Old Testament (largest, 39 books)
2. **Phase 1B** - New Testament (27 books)
3. **Phase 1C** - Book of Mormon (15 books)
4. **Phase 1D** - Doctrine & Covenants (single extraction)
5. **Phase 1E** - Pearl of Great Price (5 books)
6. **Phase 1F** - Topical Guide (for Phase 6 integration)

Commit after each sub-phase completes.

## Spanish Extraction

After English is complete and validated:
1. Verify Spanish PDF has similar TOC structure
2. Adjust page numbers if different
3. Run same extraction process
4. Validate output

## Success Criteria

- [ ] All English standard works extracted
- [ ] All Spanish standard works extracted
- [ ] Markdown preserves chapter/verse structure
- [ ] Content parseable for Phase 2 ingestion
