# Phase 3: Embedding Generation Design

**Date:** 2026-01-11

## Summary

Generate vector embeddings for all scripture verses and CFM lessons using Azure OpenAI's text-embedding-3-small model, stored in PostgreSQL with pgvector.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Embedding API | Azure OpenAI | Already have Azure setup, same endpoint/key |
| Model | text-embedding-3-small | 1536 dimensions, cost-effective (~$0.04 for 42K verses) |
| Deployment | Add to existing resource | Simpler than new resource, same billing |
| Context format | Hybrid (reference + context) | `"1 Nephi 1:1-3: [verse text]..."` |
| Batch strategy | Simple sequential | One-time job, no need for complexity |
| Context window | ±2 verses, same chapter | Balance between context and token usage |

## File Structure

```
infra/
├── modules/
│   └── openai-embedding-deployment.bicep
└── deploy-embedding.bicep

.github/workflows/
└── deploy-embedding-model.yml

src/embeddings/
├── __init__.py
├── client.py         # Azure OpenAI embedding client
├── context.py        # Context window generation
├── generate.py       # Main embedding script
└── verify.py         # Verification script

src/db/alembic/versions/
├── 002_add_vector_indexes.py      # Original IVFFlat (superseded)
└── 005_switch_to_hnsw_indexes.py  # Current HNSW indexes
```

## Infrastructure

### Bicep Deployment

Deploy `text-embedding-3-small` to existing `aif-vozloop-preprod-001` resource:

```bicep
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: existingOpenAI
  name: 'text-embedding-3-small'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-small'
      version: '1'
    }
  }
  sku: {
    name: 'Standard'
    capacity: 120  // 120K tokens per minute
  }
}
```

### GitHub Action

Manual trigger workflow that:
1. Authenticates to Azure (OIDC or service principal)
2. Runs Bicep deployment
3. Outputs deployment name

### .env Addition

```
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

## Embedding Service

### client.py

```python
from openai import AzureOpenAI

def get_embedding_client():
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )

def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings for a batch of texts."""
    client = get_embedding_client()
    response = client.embeddings.create(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        input=texts
    )
    return [item.embedding for item in response.data]
```

### context.py

```python
def build_context_text(verse, prev_verses: list, next_verses: list) -> str:
    """Build hybrid context: reference prefix + surrounding verses.

    Format: "1 Nephi 1:1-3: [v1] [v2] [v3]"

    - Only includes verses from same chapter
    - ±2 verses context window
    """
    # Determine verse range
    start_verse = prev_verses[0].verse if prev_verses else verse.verse
    end_verse = next_verses[-1].verse if next_verses else verse.verse

    # Build reference
    book_title = format_book_title(verse.book)  # "1nephi" -> "1 Nephi"
    ref = f"{book_title} {verse.chapter}:{start_verse}-{end_verse}"

    # Concatenate verse texts
    all_verses = prev_verses + [verse] + next_verses
    text = " ".join(v.text for v in all_verses)

    return f"{ref}: {text}"
```

### generate.py

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en", "es"], required=True)
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    with get_session() as session:
        # 1. Get verses without embeddings
        verses = get_verses_without_embeddings(session, args.lang)

        # 2. Process in batches
        for i in range(0, len(verses), args.batch_size):
            batch = verses[i:i + args.batch_size]

            # Build context texts
            texts = [build_context_for_verse(session, v) for v in batch]

            # Get embeddings
            embeddings = get_embeddings(texts)

            # Update database
            for verse, context, embedding in zip(batch, texts, embeddings):
                verse.context_text = context
                verse.embedding = embedding

            session.commit()
            print(f"Processed {i + len(batch)}/{len(verses)}")

            time.sleep(1)  # Rate limit safety
```

## Vector Index

**UPDATE (2026-01-13):** We switched from IVFFlat to HNSW indexes. See [ADR-001](../documentation/ADR/ADR-001-HNSW-VECTOR-INDEX.md) for the decision rationale.

**Why HNSW:** IVFFlat clusters vectors into buckets and can miss relevant results in other clusters. During evaluation, we found that queries for "liahona" missed Alma 37:38 (the primary liahona verse) because it was in a different cluster. HNSW uses a navigable graph structure that provides consistently high recall without tuning.

### Current Index (Migration 005)

```python
def upgrade():
    # HNSW index for approximate nearest neighbor search
    # m=16: connections per node (default, good balance)
    # ef_construction=64: build-time search width
    op.execute("""
        CREATE INDEX idx_scriptures_embedding
        ON scriptures
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    op.execute("""
        CREATE INDEX idx_cfm_embedding
        ON cfm_lessons
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
```

### Legacy: Migration 002 (IVFFlat - Superseded)

The original IVFFlat indexes were created in migration 002 and replaced by HNSW in migration 005.

## Verification

### verify.py

1. **Count check**: Verses with embeddings vs total
2. **Dimension check**: Verify all embeddings are 1536 dimensions
3. **Semantic search test**:
   - Query: "faith in Jesus Christ"
   - Expected: Verses from Alma 32, Ether 12, Moroni 7, etc.
4. **Sample output**: Display top 5 results with similarity scores

## Usage

```bash
# 1. Deploy embedding model (one-time)
gh workflow run deploy-embedding-model.yml

# 2. Add deployment name to .env
echo "AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small" >> .env

# 3. Generate embeddings (~15-30 min for EN)
python -m src.embeddings.generate --lang en

# 4. Add vector index (run AFTER embeddings are generated)
cd src/db && alembic upgrade head

# 5. Verify
python -m src.embeddings.verify
```

**Note**: CFM lesson embeddings are planned but not yet implemented. The current generator handles scripture verses only.

## Cost Estimate

- ~42K verses × ~150 tokens avg (with context) = ~6.3M tokens
- text-embedding-3-small: $0.02 / 1M tokens
- **Total: ~$0.13 for English**
- With Spanish: ~$0.26 total

## Success Criteria

- [ ] Embedding model deployed to Azure
- [ ] All EN verses have embeddings (41,995)
- [ ] All CFM lessons have embeddings (58)
- [ ] Vector index created
- [ ] Semantic search returns relevant results
