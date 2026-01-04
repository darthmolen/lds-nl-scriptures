# Phase 2: Data Ingestion

## Objective

Parse converted markdown files and load scripture data into PostgreSQL database.

## High-Level Tasks

1. **Schema Creation**
   - Create `scriptures` table with book, chapter, verse, text fields
   - Set up pgvector extension for embedding column
   - Create indexes for efficient querying

2. **Markdown Parser**
   - Build parser to extract individual verses from markdown
   - Handle book/chapter/verse structure detection
   - Support both English and Spanish content

3. **Context Window Generation**
   - For each verse, capture ±2 surrounding verses
   - Store as `context_text` for richer embeddings

4. **Data Loading**
   - Batch insert verses into database
   - Validate counts match expected verse totals
   - Handle language tagging (EN/ES)

## Dependencies

- Phase 1 completed (markdown files ready)
- PostgreSQL with pgvector extension
- Python database libraries (psycopg2/asyncpg, SQLAlchemy)

## Success Criteria

- All verses from both language quads loaded
- Context windows properly generated
- Database queryable by book/chapter/verse
