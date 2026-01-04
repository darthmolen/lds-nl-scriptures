# Scripture Search Project

## Architecture Decisions
- pgvector in existing Postgres (no separate vector db)
- text-embedding-3-small for embeddings
- gpt-4o-mini for generation
- Scriptures: verse-level chunks with ±2 verse context
- Topical Guide: relational, not vector
- Come Follow Me: separate table, yearly refresh
- **Languages**: English and Spanish (multi-lingual)
- **Auth**: Azure Entra ID (private, may go public later)
- **API**: Python FastAPI

## Data Sources
- Scripture quads: PDF → Markdown (via pymupdf4llm, incremental by book)
- Topical Guide: Embedded in quad PDF (pages 1606-2187)
- Come Follow Me manuals: PDF → Markdown
- Raw PDFs in `content/raw/`, processed markdown in `content/processed/`

## Project Roadmap
See `planning/roadmap.md` for detailed phases.

## Schema

```sql
CREATE EXTENSION vector;

CREATE TABLE scriptures (
    id SERIAL PRIMARY KEY,
    book VARCHAR(50),
    chapter INT,
    verse INT,
    text TEXT,
    lang VARCHAR(5),  -- 'en', 'es'
    embedding vector(1536),
    -- context window: surrounding verses for richer retrieval
    context_text TEXT
);

CREATE INDEX ON scriptures USING ivfflat (embedding vector_cosine_ops);

CREATE TABLE topical_guide (
    topic VARCHAR(255),
    scripture_id INT REFERENCES scriptures(id),
    subtopic VARCHAR(255)
);

-- Query: "What topics reference Alma 42:15?"
-- Query: "All verses under 'Atonement > Repentance'"
```

## Flow
Query → embed → pgvector search → topical guide lookup → generate with citations

### Flow diagram

```
User: "Verses about justice and mercy being reconciled"
          │
          ▼
    ┌─────────────────┐
    │ Embed query     │
    │ (3-small)       │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ pgvector search │──► Top 10 scripture chunks
    │ scriptures      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Topical Guide   │──► Related topics: Justice, Mercy, Atonement
    │ lookup          │──► Additional verses from those topics
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ gpt-4o-mini     │──► Synthesized answer with citations
    │ generation      │
    └─────────────────┘
```

### Chunking Strategy

```python
def create_embedding_text(book, chapter, verse, text, prev_verse, next_verse):
    return f"""
    {book} {chapter}:{verse}
    Context: {prev_verse}
    Verse: {text}
    Following: {next_verse}
    """
```

## Constraints
- Shoestring budget
- Already have Postgres, AKS, AI Foundry
- Prove concept, potentially donate to church
