# Phase 2: Data Ingestion

## Objective

Load structured scripture and CFM data from Phase 1 JSON files into PostgreSQL with pgvector.

## Input Data

From Phase 1, we have structured JSON (not markdown):

```text
content/processed/
├── scriptures/{en,es}/
│   ├── oldtestament.json
│   ├── newtestament.json
│   ├── bookofmormon.json
│   ├── doctrineandcovenants.json
│   └── pearlofgreatprice.json
└── cfm/{en,es}/
    └── cfm_{ot,dc,bom,nt}_{year}.json
```

**Scripture JSON structure:**

```json
{
  "title": "Book of Mormon",
  "books": {
    "1nephi": {
      "title": "1 Nephi",
      "chapters": {
        "1": {
          "summary": "Nephi begins the record...",
          "verses": [
            {
              "text": "I, Nephi, having been born of goodly parents...",
              "footnotes": [
                {"footnote": "TG Birthright.", "start": 22, "end": 26}
              ]
            }
          ]
        }
      }
    }
  }
}
```

## High-Level Tasks

1. **Schema Creation**
   - Create `scriptures` table (book, chapter, verse, text, lang, footnotes JSONB)
   - Set up pgvector extension for embedding column
   - Create `cfm_lessons` table for Come Follow Me content
   - Create indexes for querying and vector search

2. **Scripture Loader**
   - Read JSON files directly (no parsing needed)
   - Insert verses with footnotes as JSONB
   - Generate context windows (±2 verses)
   - Tag with language code

3. **CFM Loader**
   - Load lesson content from JSON
   - Link to scripture references where possible

4. **Validation**
   - Verify verse counts match Phase 1 totals (~42K per language)
   - Spot-check footnote integrity
   - Test basic queries

## Updated Schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE scriptures (
    id SERIAL PRIMARY KEY,
    volume VARCHAR(50),      -- oldtestament, bookofmormon, etc.
    book VARCHAR(50),        -- genesis, 1nephi, etc.
    chapter INT,
    verse INT,
    text TEXT NOT NULL,
    lang VARCHAR(5) NOT NULL, -- 'en', 'es'
    footnotes JSONB,          -- Already structured from API
    context_text TEXT,        -- ±2 verses for embedding
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cfm_lessons (
    id SERIAL PRIMARY KEY,
    year INT,
    lesson_id VARCHAR(100),
    title TEXT,
    date_range VARCHAR(100),
    scripture_refs TEXT[],
    content TEXT,
    lang VARCHAR(5),
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scriptures_ref ON scriptures(book, chapter, verse, lang);
CREATE INDEX idx_scriptures_lang ON scriptures(lang);
CREATE INDEX idx_cfm_year_lang ON cfm_lessons(year, lang);
```

## Dependencies

- Phase 1 completed (JSON files ready)
- PostgreSQL with pgvector extension
- Python: psycopg2 or asyncpg

## Success Criteria

- [ ] All verses loaded (~42K EN, ~42K ES)
- [ ] Footnotes preserved as JSONB
- [ ] Context windows generated
- [ ] CFM lessons loaded
- [ ] Basic queries working (lookup by reference, search by lang)
