# Search Tuning Variables Reference

This document explains all the configurable variables ("knobs") that affect scripture search quality. Understanding these helps you reason about what changes will improve precision.

## Quick Reference Table

| Variable | Location | Current Value | Range | What It Controls |
|----------|----------|---------------|-------|------------------|
| **Embedding Model** | `src/embeddings/client.py` | `text-embedding-3-small` | Model choice | Semantic representation quality |
| **Embedding Dimensions** | Fixed by model | 1536 | Fixed | Vector size |
| **HNSW ef_search** | PostgreSQL runtime | 40 (default) | 10-100+ | Query-time recall vs speed |
| **vector_weight** | `src/api/services/search.py:16` | 0.7 | 0.0-1.0 | Vector vs text importance |
| **search_limit multiplier** | `src/api/services/search.py:224` | 3x | 1x-10x | Candidate pool size |
| **min_word_length** | `src/api/services/search.py:160` | 3 | 1-5 | Text search word filter |
| **precision@5 threshold** | `src/evaluation/config.py` | 0.75 | 0.0-1.0 | Pass/fail bar |
| **precision@10 threshold** | `src/evaluation/config.py` | 0.70 | 0.0-1.0 | Pass/fail bar |

---

## 1. Embedding Model

**What it is:** The neural network that converts text into 1536-dimensional vectors.

**Current:** `text-embedding-3-small` (Azure OpenAI)

**Alternatives:**
| Model | Dimensions | Pros | Cons |
|-------|------------|------|------|
| text-embedding-3-small | 1536 | Fast, cheap, good | Less nuanced |
| text-embedding-3-large | 3072 | More accurate | 2x cost, slower |
| text-embedding-ada-002 | 1536 | Legacy, stable | Older technology |

**Effect of changing:**
- **Larger model →** Better semantic understanding, especially for theological nuance
- **Smaller model →** Faster, cheaper, may miss subtle connections

**Trade-off:** The embedding model is foundational. Changing it requires re-embedding all ~42,000 verses.

---

## 2. HNSW Index Parameters

**What it is:** HNSW (Hierarchical Navigable Small World) is a graph-based index for approximate nearest neighbor search. Unlike IVFFlat (which clusters vectors into buckets), HNSW builds a navigable graph where similar vectors are connected.

**Why HNSW over IVFFlat:** We switched from IVFFlat after discovering recall failures. IVFFlat clusters vectors into buckets and only searches nearby buckets at query time. This caused relevant verses (like Alma 37:38 for "liahona") to be missed because they were in different clusters. See [ADR-001](ADR/ADR-001-HNSW-VECTOR-INDEX.md) for full details.

### Build-time Parameters (set during index creation)

| Parameter | Current | Range | Effect |
|-----------|---------|-------|--------|
| **m** | 16 | 4-64 | Connections per node. Higher = better recall, more memory |
| **ef_construction** | 64 | 16-256 | Search width during build. Higher = better index quality, slower build |

**Location:** `src/db/alembic/versions/005_switch_to_hnsw_indexes.py`

### Query-time Parameter

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| **hnsw.ef_search** | 40 | 10-100+ | Search width at query time. Higher = better recall, slower |

**How to adjust at runtime:**
```sql
SET hnsw.ef_search = 100;  -- Higher recall for important queries
```

**Effect of changing:**
- **Higher ef_search →** Better recall (finds more relevant results), slower queries
- **Lower ef_search →** Faster queries, may miss some results

**Current status:** Using pgvector defaults (m=16, ef_construction=64, ef_search=40). These work well for our ~42K vector dataset. No runtime tuning needed - HNSW provides consistently good recall without adjustment.

---

## 3. Vector Weight (`vector_weight`)

**What it is:** How much to favor semantic (vector) similarity vs exact term matching (text).

**Location:** `src/api/services/search.py:16`

**Current:** 0.7 (70% vector, 30% text)

**Formula:**
```
hybrid_score = vector_weight × vector_similarity + (1 - vector_weight) × text_rank
```

| Weight | Meaning | Good for |
|--------|---------|----------|
| 1.0 | Pure vector search | Conceptual queries ("teachings about love") |
| 0.7 | Mostly semantic | General use - balances both |
| 0.5 | Equal weight | When terms matter as much as meaning |
| 0.3 | Mostly text | Specific term searches ("liahona") |
| 0.0 | Pure text search | Exact phrase matching |

**Effect of changing:**
- **Higher (→1.0) →** Prioritizes conceptual similarity, may miss exact term matches
- **Lower (→0.0) →** Prioritizes keyword matching, may miss semantically related verses without exact terms

**Current problem:** Theological inference queries (score: 10%) need semantic understanding, but specific terms (liahona) need keyword matching. 0.7 balances these.

---

## 4. Search Limit Multiplier

**What it is:** How many candidates to fetch from each search type before merging.

**Location:** `src/api/services/search.py:224`

**Current:** `limit × 3` (if limit=10, fetch 30 from vector + 30 from text)

**How hybrid search works:**
```
1. Get top N×3 candidates from vector search
2. Get top N×3 candidates from text search
3. UNION (deduplicate)
4. Score ALL candidates with BOTH methods
5. Return top N by hybrid score
```

| Multiplier | Candidate Pool | Effect |
|------------|----------------|--------|
| 1x | limit | Minimal - may miss good hybrid matches |
| 3x | limit × 3 | Balanced - good coverage |
| 5x | limit × 5 | More thorough - slower |
| 10x | limit × 10 | Very thorough - noticeably slower |

**Effect of changing:**
- **Higher →** More candidates to consider, better chance of finding optimal hybrid matches
- **Lower →** Faster, but may miss candidates that score well on the "other" method

---

## 5. Minimum Word Length Filter

**What it is:** Shortest word to include in text search queries.

**Location:** `src/api/services/search.py:160`

**Current:** 3 characters

**Example:**
```
Query: "the tree of life"
After filter (min=3): "tree | life"  (drops "the", "of")
```

| Min Length | Kept | Dropped |
|------------|------|---------|
| 1 | All words | None |
| 2 | "of", "to", "in" | "a", "I" |
| 3 | "the", "and", "for" | Short prepositions |
| 4 | Meaningful words only | "the", "and", etc. |

**Effect of changing:**
- **Higher →** Fewer, more meaningful keywords; may lose important short terms
- **Lower →** More terms, but includes noise words that match everywhere

---

## 6. PostgreSQL Text Search Configuration

**What it is:** Language-specific stemming and stop-word handling.

**Location:** `src/api/services/search.py:154`

**Current:** `english` for en, `spanish` for es

**What it does:**
```
"repentance" → stems to "repent"
"loving" → stems to "love"
Matches: "repent", "repents", "repented", "repentance"
```

**Effect:** Proper language config means "repentance" finds "repent" and vice versa.

---

## 7. Text Search Ranking Function

**What it is:** How to score text matches.

**Location:** `src/api/services/search.py:200`

**Current:** `ts_rank_cd` (cover density)

**Options:**
| Function | Description |
|----------|-------------|
| `ts_rank` | Simple occurrence counting |
| `ts_rank_cd` | Cover density - rewards matches close together |

**Effect:** `ts_rank_cd` prefers "liahona compass ball" all in one verse over verses with just one of those terms scattered about.

---

## 8. Evaluation Thresholds

**What they are:** The precision scores we need to achieve to "pass".

**Location:** `src/evaluation/config.py`

| Metric | Threshold | Current Score | Status |
|--------|-----------|---------------|--------|
| Precision@5 | 75% | 57.2% | FAIL |
| Precision@10 | 70% | 48.6% | FAIL |

**What precision means:**
```
Precision@10 = (relevant results in top 10) / 10

With LLM scoring (normalized):
- Score 3 (highly relevant) = 1.0
- Score 2 (partially relevant) = 0.5
- Score 1 (not relevant) = 0.0

Precision@10 = sum of normalized scores / 10
```

**Effect of changing:**
- **Higher thresholds →** Harder to pass, requires better retrieval
- **Lower thresholds →** Easier to pass, may accept mediocre results

---

## 9. LLM Judge Model

**What it is:** The model that evaluates whether retrieved verses are relevant.

**Location:** `src/evaluation/llm_local/start.sh`

**Current:** Qwen2.5-7B-Instruct (or 14B)

**Effect of changing:**
- **Larger model →** More nuanced theological judgment, more expensive/slower
- **Smaller model →** Faster evaluation, may miss subtle relevance

**Note:** The judge doesn't affect search quality - it only measures it.

---

## 10. Relevance Scoring Rubric

**What it is:** How the LLM judge converts relevance to a 1-3 score.

**Location:** `src/evaluation/retrieval.py:27-51`

**Current scale:**
| Score | Label | Meaning | Normalized |
|-------|-------|---------|------------|
| 3 | Highly Relevant | Direct match to query/criteria | 1.0 |
| 2 | Partially Relevant | Related but not primary | 0.5 |
| 1 | Not Relevant | Unrelated or superficial | 0.0 |

**Effect of changing:**
- **Stricter rubric →** Lower precision scores (harder to get 3s)
- **Lenient rubric →** Higher precision scores (more 2s and 3s)

---

## Current Results by Category

| Category | P@10 | Primary Issue |
|----------|------|---------------|
| specific_term | 63.7% | Fixed by hybrid search (was 0%) |
| cross_volume | 65.0% | Near target |
| doctrinal_concept | 49.0% | Needs semantic boost |
| narrative | 40.0% | Story context not captured |
| theological_inference | 10.0% | Hardest - needs reasoning |

---

## Improvement Options (Not Yet Tried)

| Option | Variables Changed | Expected Effect |
|--------|-------------------|-----------------|
| Lower vector_weight (0.5) | vector_weight | Better for specific terms, worse for concepts |
| Query expansion | Add synonyms before search | More term matches |
| Re-rank with LLM | Post-process top-N | Better precision, slower |
| Larger embedding model | Embedding model | Better semantics, costly re-embed |
| Chunking strategy | How verses are stored | Better context, complex |

---

## How to Experiment

1. **Single variable change:** Modify one knob, re-run evaluation
2. **Compare:** Look at category breakdown, not just overall
3. **Commit:** Each experiment on separate branch
4. **Document:** Record what changed and the result

Example:
```bash
# Try vector_weight = 0.5
# Edit src/api/services/search.py line 16
# DEFAULT_VECTOR_WEIGHT = 0.5

# Run evaluation
./src/evaluation/llm_local/start.sh  # In another terminal
source .venv/bin/activate && python scripts/run_precision_eval.py
```
