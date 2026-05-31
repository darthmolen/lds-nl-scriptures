# Phase: Search Precision Tuning Experiments

**Date:** 2026-01-13
**Branch:** feature/hybrid-search
**Objective:** Improve retrieval precision from current 45.8% P@10 toward 70% target

## Baseline (Current State)

| Metric | Score | Target | Gap |
|--------|-------|--------|-----|
| Precision@5 | 55.6% | 75% | -19.4% |
| Precision@10 | 45.8% | 70% | -24.2% |

**Category breakdown:**
| Category | P@10 | Notes |
|----------|------|-------|
| cross_volume | 63.3% | Near target |
| specific_term | 55.0% | Keyword matching helps |
| doctrinal_concept | 50.0% | Semantic understanding needed |
| narrative | 38.8% | Story context not captured |
| theological_inference | 5.0% | Hardest - needs reasoning |

## Experiments (Order of Precedence)

### Experiment 1: vector_weight = 0.5 (Equal Balance) ✓ COMPLETE
- [x] Change `DEFAULT_VECTOR_WEIGHT` from 0.7 to 0.5
- [x] Run precision evaluation
- [x] Record results
- [x] Decision: **KEEP** - improved P@10

**Results:** P@5: 53.9%, P@10: 49.7% (+3.9%), theological_inference: 5.0%, specific_term: 60.0%

**File:** `src/api/services/search.py:16`

---

### Experiment 2: Query Expansion (Theological Synonyms) ✓ COMPLETE
- [x] Design synonym mapping for theological terms
- [x] Implement query expansion before embedding
- [x] Run precision evaluation (A: weight=0.5, B: weight=0.7)
- [x] Record results
- [x] Decision: **KEEP** with weight=0.5 (Exp 2A)

**Results:**
- Exp 2A (0.5 + expansion): P@5: 54.4%, P@10: 50.0%, theological_inference: 12.5%
- Exp 2B (0.7 + expansion): P@5: 56.1%, P@10: 46.1%, theological_inference: 10.0%

**Files created:**
- `src/api/services/query_expansion.py` - Theological synonym mappings

---

### Experiment 3: LLM Re-ranking ⏭️ SKIPPED
Skipped - adds per-query latency/cost. Proceeding to nuclear option instead.

---

### Experiment 4: Larger Embedding Model (Nuclear Option) → NEXT
- [ ] Deploy text-embedding-3-large to Azure
- [ ] Re-embed all verses (~$0.52)
- [ ] Update vector column dimensions (1536 → 3072)
- [ ] Run precision evaluation
- [ ] Record results

**See:** `planning/in_progress/phase_large_embeddings_2026-01-13.md`

---

## Results Tracking

| Experiment | P@5 | P@10 | theological_inference | specific_term | Decision |
|------------|-----|------|----------------------|---------------|----------|
| Baseline (0.7 weight, HNSW) | 55.6% | 45.8% | 5.0% | 55.0% | - |
| Exp 1: weight=0.5 | 53.9% | 49.7% | 5.0% | 60.0% | KEEP |
| Exp 2A: expansion + 0.5 | 54.4% | 50.0% | 12.5% | 60.0% | **KEEP** |
| Exp 2B: expansion + 0.7 | 56.1% | 46.1% | 10.0% | 55.0% | - |
| Exp 3: LLM re-rank | - | - | - | - | SKIPPED |
| Exp 4: large embeddings | | | | | PENDING |

## Current Best Configuration

```python
# src/api/services/search.py
DEFAULT_VECTOR_WEIGHT = 0.5
ENABLE_QUERY_EXPANSION = True
```

**Current P@10: 50.0%** (target: 70%, gap: 20%)

## Success Criteria

- P@10 ≥ 70% overall
- theological_inference ≥ 30% (currently 12.5%)
- No significant regression in other categories

## Notes

- LLM judge has some variability between runs (~5% variance observed)
- Reports saved to `src/evaluation/reports/`
- Query expansion helped theological_inference from 5% → 12.5%
