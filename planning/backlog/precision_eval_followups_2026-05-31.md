# Backlog: Precision Eval — Large-Embeddings Experiment Follow-ups

**Created:** 2026-05-31
**Branch:** feature/hybrid-search
**Source phases:**
- `planning/in_progress/phase_search_tuning_2026-01-13.md`
- `planning/completed/phase_large_embeddings_2026-01-13.md`

## Context: What Was Run

A series of retrieval-precision tuning experiments using the LLM-as-judge
harness (`src/evaluation/retrieval.py`, driven by `scripts/run_precision_eval.py`).
Ground truth: 18 queries across 5 categories in
`tests/evaluation/golden/retrieval_ground_truth.json`. Reports land in
`src/evaluation/reports/`.

| Experiment | P@5 | P@10 | theological_inference | Decision |
|------------|-----|------|----------------------|----------|
| Baseline (vector_weight=0.7, HNSW) | 55.6% | 45.8% | 5.0% | — |
| Exp 1: vector_weight=0.5 | 53.9% | 49.7% | 5.0% | KEEP |
| Exp 2A: query expansion + 0.5 | 54.4% | 50.0% | 12.5% | **KEEP** |
| Exp 2B: query expansion + 0.7 | 56.1% | 46.1% | 10.0% | — |
| Exp 3: LLM re-rank | — | — | — | SKIPPED (cost/latency) |
| Exp 4: large embeddings (3-large @ 2000d) | 60.0% | 53.6% | 17.5% | modest gain, kept |

**Current best:** P@10 = 53.6%, still **16.4 points below the 70% target**.
`theological_inference` remains the weakest category (17.5% vs 30% target).

### What the code actually does (verified 2026-05-31)
- `src/db/models.py`: `VECTOR_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "2000"))`,
  applied to all vector columns.
- `src/db/alembic/versions/006_expand_vector_dimensions.py`: alters columns to
  `vector(2000)` and NULLs existing embeddings (re-embed required).
- `src/embeddings/client.py`: `EMBEDDING_DIMENSIONS` default 2000; `get_embeddings`
  now passes `dimensions=` to the Azure OpenAI call.
- pgvector HNSW caps at 2000 dims, so `text-embedding-3-large`'s native 3072 is
  truncated to 2000 (not the 3072 the original plan assumed).

## What Still Needs To Be Checked

### 1. Report config block is hardcoded — exp4 reports are mislabeled (HIGH)
`scripts/run_precision_eval.py` `get_search_config()` hardcodes:
```python
"embedding_model": "text-embedding-3-small",
"embedding_dimensions": 1536,
```
So `precision_eval_*_exp4_large_embeddings_2000d.txt` reports the config as
**1536d / 3-small** even though the experiment's whole point was 2000d / 3-large.
- [ ] Make `get_search_config()` read the real values from env / `models.VECTOR_DIMENSIONS`
      / `client.EMBEDDING_DIMENSIONS` / `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` instead of literals.
- [ ] Re-run exp4 (or annotate the existing reports) so the recorded config is trustworthy.

### 2. Confirm exp4 actually ran on large-model 2000d vectors (HIGH)
Because the report config is unreliable, independently verify the stored vectors
backing the exp4 numbers were really `text-embedding-3-large` @ 2000d:
- [ ] Check live DB column type: `SELECT atttypmod FROM pg_attribute WHERE attrelid='scriptures'::regclass AND attname='embedding';` (expect 2000).
- [ ] Confirm `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` pointed at the large deployment
      during re-embed — note `client.py` still defaults the *deployment name* to
      `text-embedding-3-small`. (3-small cannot return 2000 dims, so if vectors exist
      at 2000d the large model must have been used — confirm, don't assume.)
- [ ] Confirm `text-embedding-3-large` was actually deployed to Azure
      (`infra/modules/openai-embedding-deployment.bicep` change + portal/CLI).

### 3. Spanish embeddings status (MEDIUM)
Re-embed steps in the phase doc only ran `--lang en`. After migration 006 NULLed
all embeddings:
- [ ] Verify whether `es` verses were re-embedded at 2000d or are still NULL.
- [ ] If NULL, Spanish vector search is currently broken — schedule a re-embed.

### 4. Migration docstring/comment drift (LOW)
`006_expand_vector_dimensions.py` line ~38 comment still reads `1536 -> 3072`
while the executed DDL is `vector(2000)`. Downgrade reverts to 1536.
- [ ] Fix the misleading comment.

### 5. `embeddings_backup_small.dump` (304 MB) — rollback artifact (HOUSEKEEPING)
This is the pre-migration dump of the old 1536d small-model embeddings, kept for
the rollback plan. It is **gitignored** (too large for the repo).
- [ ] Decide on a durable home (blob storage / off-repo backup) and document its
      location, or delete once the large-embedding direction is confirmed.

## Bigger Question (for a future phase, not this backlog)
Large embeddings bought only +3.6% P@10. Reaching 70% / 30%-theological likely
needs a different lever than embedding size — candidates: LLM re-ranking (Exp 3,
previously skipped), better chunk/context construction, hybrid weight tuning per
category, or a domain-tuned retrieval model. Spin up a new tuning phase to decide.
