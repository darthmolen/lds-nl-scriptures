# Phase: Large Embedding Model Migration (Nuclear Option)

**Date:** 2026-01-13 (completed 2026-01-14)
**Branch:** feature/hybrid-search
**Objective:** Improve retrieval precision from 50% P@10 to 70% target by upgrading to text-embedding-3-large
**Status:** COMPLETED

## Results

| Metric | Before (small, 1536d) | After (large, 2000d) | Change |
|--------|----------------------|---------------------|--------|
| **P@10** | 50.0% | **53.6%** | +3.6% |
| theological_inference | 12.5% | 17.5% | +5.0% |
| specific_term | ~50% | 66.2% | +16% |
| cross_volume | ~45% | 58.3% | +13% |
| doctrinal_concept | ~55% | 61.0% | +6% |
| narrative | ~45% | 46.2% | +1% |

**Outcome:** Modest improvement. Still 16.4 points below 70% target.

### Key Finding: HNSW 2000 Dimension Limit
pgvector HNSW indexes have a 2000-dimension maximum. Used 2000 dims instead of 3072.

## Context

After tuning experiments (weight=0.5, query expansion), we achieved:

- P@10: 50.0% (target: 70%, gap: 20%)
- theological_inference: 12.5% (target: 30%)

The remaining gap likely requires better semantic understanding in the embeddings themselves.

## Model Comparison

| Model | Dimensions | Cost per 1M tokens | Quality |
|-------|------------|-------------------|---------|
| text-embedding-3-small | 1536 | $0.02 | Good |
| **text-embedding-3-large** | 3072 | $0.13 | Better theological nuance |

**Re-embedding cost:** ~42K verses × ~150 tokens × $0.13/1M = **~$0.82**

## Implementation Steps

### Step 1: Deploy text-embedding-3-large to Azure

Update `infra/modules/openai-embedding-deployment.bicep`:

```bicep
resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: existingOpenAI
  name: 'text-embedding-3-large'  // Changed from 'text-embedding-3-small'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'text-embedding-3-large'  // Changed
      version: '1'
    }
  }
  sku: {
    name: 'Standard'
    capacity: 120
  }
}
```

Or deploy manually via Azure Portal/CLI:

```bash
az cognitiveservices account deployment create \
  --name aif-vozloop-preprod-001 \
  --resource-group <your-rg> \
  --deployment-name text-embedding-3-large \
  --model-name text-embedding-3-large \
  --model-version 1 \
  --model-format OpenAI \
  --sku-capacity 120 \
  --sku-name Standard
```

### Step 2: Create Database Migration (1536 → 3072 dimensions)

Create `src/db/alembic/versions/006_expand_vector_dimensions.py`:

```python
"""Expand vector dimensions from 1536 to 3072 for text-embedding-3-large.

Revision ID: 006
Revises: 005
"""

from alembic import op

revision = "006"
down_revision = "005"

def upgrade() -> None:
    # Drop HNSW indexes first (required before changing column type)
    op.execute("DROP INDEX IF EXISTS idx_scriptures_embedding")
    op.execute("DROP INDEX IF EXISTS idx_cfm_embedding")

    # Change column dimensions: 1536 -> 3072
    op.execute("ALTER TABLE scriptures ALTER COLUMN embedding TYPE vector(3072)")
    op.execute("ALTER TABLE cfm_lessons ALTER COLUMN embedding TYPE vector(3072)")

    # Set all embeddings to NULL (must re-embed with new model)
    op.execute("UPDATE scriptures SET embedding = NULL")
    op.execute("UPDATE cfm_lessons SET embedding = NULL")

    # Recreate HNSW indexes (will be empty until re-embedding)
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

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_scriptures_embedding")
    op.execute("DROP INDEX IF EXISTS idx_cfm_embedding")

    op.execute("UPDATE scriptures SET embedding = NULL")
    op.execute("UPDATE cfm_lessons SET embedding = NULL")

    op.execute("ALTER TABLE scriptures ALTER COLUMN embedding TYPE vector(1536)")
    op.execute("ALTER TABLE cfm_lessons ALTER COLUMN embedding TYPE vector(1536)")

    op.execute("""
        CREATE INDEX idx_scriptures_embedding
        ON scriptures USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    op.execute("""
        CREATE INDEX idx_cfm_embedding
        ON cfm_lessons USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
```

### Step 3: Update Embedding Client

Update `src/embeddings/client.py` to use the new deployment:

```python
# Change deployment name
EMBEDDING_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
    "text-embedding-3-large"  # Changed default
)
```

Update `.env`:

```
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
```

### Step 4: Re-embed All Verses

```bash
# Run migration first
cd src/db && alembic upgrade head

# Re-generate embeddings (will take ~30-60 min)
python -m src.embeddings.generate --lang en

# Verify
python -m src.embeddings.verify
```

### Step 5: Run Precision Evaluation

```bash
# Start Qwen2 judge
./src/evaluation/llm_local/start.sh

# Run evaluation
python scripts/run_precision_eval.py --name "exp4_large_embeddings"
```

### Step 6: Update Documentation

If successful, update:

- `documentation/SEARCH-TUNING-VARIABLES.md` - Change embedding model reference
- `documentation/SYSTEM-ARCHITECTURE.md` - Update vector dimensions
- `planning/in_progress/phase_search_tuning_2026-01-13.md` - Record results

## Checklist

- [ ] Deploy text-embedding-3-large model to Azure OpenAI
- [ ] Create and run migration 006 (expand to 3072 dimensions)
- [ ] Update `.env` with new deployment name
- [ ] Re-embed all English verses (~42K)
- [ ] Verify embeddings (count + dimensions)
- [ ] Run precision evaluation
- [ ] Record results in tuning plan
- [ ] Update documentation if keeping

## Rollback Plan

If results are worse or issues occur:

```bash
# Revert migration
cd src/db && alembic downgrade 005

# Update .env back to small model
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Re-embed with original model
python -m src.embeddings.generate --lang en
```

## Success Criteria

- P@10 ≥ 70%
- theological_inference ≥ 30%
- No significant regression in other categories

## Notes

- Re-embedding is a one-time cost (~$0.82)
- Ongoing embedding costs will be ~6.5x higher ($0.13 vs $0.02 per 1M tokens)
- Storage will ~2x (3072 vs 1536 floats per vector)
- Query embedding calls will also use the large model
