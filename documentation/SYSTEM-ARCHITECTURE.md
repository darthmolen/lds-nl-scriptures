# System Architecture

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

### Flow Diagram

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
