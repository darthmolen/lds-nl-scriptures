# Phase 5b: Fix Retrieval Evaluation

**Date**: 2026-01-12
**Status**: Complete

## Problem

Phase 5a used exact verse matching for recall measurement. This is wrong for semantic search:
- A query like "faith hope charity" has 50+ relevant verses
- Picking 3 exact verses and calling everything else a "miss" is invalid
- Baseline results (Recall@5: 7.4%) were meaningless

## Solution

Replace exact-match recall with **Precision@k using LLM-as-judge** (Qwen2 via vLLM).

## Files Modified

| File | Change |
|------|--------|
| `tests/evaluation/golden/retrieval_ground_truth.json` | Replace expected_verses with relevance_rubric (18 test cases) |
| `src/evaluation/rubrics.py` | Add RETRIEVAL_RELEVANCE dimension with 1-3 scale |
| `src/evaluation/retrieval.py` | Complete rewrite: PrecisionResult, run_precision_evaluation() |
| `src/evaluation/__init__.py` | Update exports |
| `src/evaluation/config.py` | Add precision thresholds |

## New Ground Truth Format

**Before (wrong):**
```json
{
  "query": "faith hope charity",
  "expected_verses": ["1 Corinthians 13:13", "Moroni 7:1"]
}
```

**After (correct):**
```json
{
  "query": "faith hope charity",
  "relevance_rubric": "Verse discusses faith, hope, and/or charity as Christian virtues",
  "top_k": 10,
  "category": "doctrinal_concept"
}
```

## Test Case Categories (18 total)

| Category | Count | Description |
|----------|-------|-------------|
| doctrinal_concept | 5 | Abstract teachings (faith, atonement) |
| narrative | 4 | Story-based queries (tree of life) |
| specific_term | 4 | Unique vocabulary (liahona) |
| cross_volume | 3 | Concepts spanning books |
| theological_inference | 2 | Hardest - non-obvious connections |

### Theological Inference Cases (hardest)

1. **"How 'I Am' relates to 'The Word'"** - Connects Jehovah with Logos Christology
2. **"lamb, sacrificial lamb, Jesus as the Lamb of God"** - Spans literal → typological → Christological

## LLM-as-Judge Scoring

Per advanced-evaluation skill guidance:
- Chain-of-thought (reasoning BEFORE score)
- 1-3 scale normalized to 0.0-1.0
- JSON output with reasoning, score, confidence

| Score | Label | Normalized |
|-------|-------|------------|
| 3 | Highly Relevant | 1.0 |
| 2 | Somewhat Relevant | 0.5 |
| 1 | Not Relevant | 0.0 |

`Precision@k = sum(normalized_scores) / k`

## Targets

| Metric | Threshold |
|--------|-----------|
| Precision@5 | ≥ 75% |
| Precision@10 | ≥ 70% |

## Verification

1. All 66 API tests pass
2. Syntax check passes for all evaluation files
3. To run baseline: Start vLLM with Qwen2, then:
   ```python
   from src.evaluation.retrieval import run_precision_evaluation
   report = run_precision_evaluation()
   print_precision_report(report)
   ```

## Dependencies

- Qwen2.5-7B running via vLLM (port 8004)
- Azure OpenAI for query embeddings

## Progress Log

- 2026-01-12: Identified problem with exact-match recall
- 2026-01-12: Brainstormed Precision@k approach with LLM-as-judge
- 2026-01-12: Read advanced-evaluation skill for best practices
- 2026-01-12: Updated ground truth format (18 test cases)
- 2026-01-12: Added RETRIEVAL_RELEVANCE rubric
- 2026-01-12: Rewrote retrieval.py with precision evaluation
- 2026-01-12: All 66 tests pass
- 2026-01-12: Phase complete

## Next Steps

1. Start vLLM with Qwen2 and run baseline evaluation
2. If Precision@k < targets, proceed to Phase 5c (retrieval tuning)
