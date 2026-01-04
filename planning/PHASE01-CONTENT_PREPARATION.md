# Phase 1: Content Preparation

## Objective

Convert raw PDF scripture content to structured markdown format suitable for parsing and ingestion.

## Input Files

### Scriptures (Priority 1)
| File | Language | Location |
|------|----------|----------|
| lds_scriptures_quad_en.pdf | English | `content/raw/scriptures/` |
| lds_scriptures_quad_es.pdf | Spanish | `content/raw/escrituras/` |

### Come Follow Me (Priority 2 - Phase 7)
| File | Language | Location |
|------|----------|----------|
| 2024_come_follow_me_book_of_mormon_consolidated_manual_en.pdf | English | `content/raw/come-follow-me/` |
| 2025_come_follow_me_doctrine_and_covenants_en.pdf | English | `content/raw/come-follow-me/` |
| 2026_come_follow_me_old_testament_en.pdf | English | `content/raw/come-follow-me/` |
| sunday_school_manual_new_testament_2023_en.pdf | English | `content/raw/come-follow-me/` |
| (Spanish equivalents) | Spanish | `content/raw/ven-sigue-me/` |

## Output Structure

```
content/
├── raw/                    # Source PDFs (existing)
│   ├── scriptures/
│   ├── escrituras/
│   ├── come-follow-me/
│   └── ven-sigue-me/
└── processed/              # Converted markdown (new)
    ├── scriptures/
    │   ├── en/
    │   │   └── lds_scriptures_quad_en.md
    │   └── es/
    │       └── lds_scriptures_quad_es.md
    └── come-follow-me/
        ├── en/
        └── es/
```

## Conversion Tool

Using the existing Marker MCP server at `src/tools/marker_mcp/server.py`:

- **Library**: [Marker](https://github.com/VikParuchuri/marker) - high-quality PDF to markdown
- **Interface**: MCP server with `convert_pdf` and `batch_convert` tools
- **Output**: Markdown + extracted images

## Tasks

### 1.1 Environment Setup
- [ ] Install marker MCP server dependencies
- [ ] Verify GPU availability (marker benefits from CUDA)
- [ ] Test conversion on a small PDF first

### 1.2 Scripture Conversion
- [ ] Convert English quad PDF to markdown
- [ ] Convert Spanish quad PDF to markdown
- [ ] Review output quality and structure

### 1.3 Post-Processing Assessment
- [ ] Analyze markdown structure (headers, verses, chapters)
- [ ] Identify parsing patterns for verse extraction
- [ ] Document any conversion artifacts or issues
- [ ] Determine if additional cleanup scripts are needed

### 1.4 Quality Validation
- [ ] Spot-check verses across all standard works
- [ ] Verify chapter/verse numbering integrity
- [ ] Check for missing or corrupted content
- [ ] Compare sample verses against official text

## Expected Challenges

1. **Large file sizes**: Quad PDFs are 30-50MB each; conversion may take significant time
2. **Complex layouts**: Footnotes, cross-references, chapter headings
3. **Two-column format**: Scripture pages often use two columns
4. **Verse numbering**: Need to preserve verse numbers for citation

## Success Criteria

- [ ] Both quad PDFs successfully converted to markdown
- [ ] Markdown preserves book/chapter/verse structure identifiably
- [ ] Content is readable and parseable for Phase 2 ingestion
- [ ] Images extracted (if any) and referenced correctly

## Dependencies

- Python 3.10+
- marker library (`pip install marker-pdf`)
- PyTorch (for marker's ML models)
- Optional: CUDA for GPU acceleration

## Notes

- Marker uses ML models for layout detection; first run downloads ~2GB of models
- Consider running conversion on a machine with GPU for faster processing
- Come Follow Me PDFs will be converted in Phase 7, not Phase 1
