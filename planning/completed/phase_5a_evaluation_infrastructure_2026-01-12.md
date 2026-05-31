# Phase 5a: Evaluation Infrastructure

**Date**: 2026-01-12
**Status**: Complete

## Objective

Set up LLM-as-judge evaluation framework using local Qwen2 via vLLM, with 5 rubrics for scripture RAG evaluation. Also implement retrieval recall measurement and RAG generation endpoint.

## Approach

Test-first: Build evaluation infrastructure before RAG generation so we can measure quality from the start.

## Files Created

### Evaluation Framework
- [x] `src/evaluation/__init__.py` - Package exports
- [x] `src/evaluation/llm_local/start.sh` - vLLM startup (port 8004)
- [x] `src/evaluation/config.py` - Evaluation settings
- [x] `src/evaluation/judge.py` - Qwen2 judge client
- [x] `src/evaluation/rubrics.py` - 5 rubric definitions with prompts
- [x] `src/evaluation/runner.py` - Evaluation runner
- [x] `src/evaluation/retrieval.py` - Recall measurement

### Golden Test Sets
- [x] `tests/evaluation/__init__.py`
- [x] `tests/evaluation/golden/schema.json` - Test case schema
- [x] `tests/evaluation/golden/scripture_qa.json` - 20 Q&A pairs
- [x] `tests/evaluation/golden/retrieval_ground_truth.json` - 18 recall test cases

### RAG Generation
- [x] `src/api/schemas/generation.py` - AskRequest/AskResponse models
- [x] `src/api/services/generation.py` - GenerationService
- [x] `src/api/routers/ask.py` - POST /api/v1/ask endpoint
- [x] `src/api/prompts/scripture_assistant.py` - System prompt
- [x] `src/api/prompts/__init__.py` - Package init

## 5 Evaluation Rubrics

1. **factual_accuracy** (weight: 0.25) - Claims match scripture content
2. **citation_accuracy** (weight: 0.25) - Citations support claims made
3. **completeness** (weight: 0.20) - Covers question fully
4. **source_relevance** (weight: 0.15) - Uses relevant vs tangential scripture
5. **theological_appropriateness** (weight: 0.15) - Doctrinally sound interpretation

## Baseline Results

### Retrieval Recall (2026-01-12)

| Metric | Score | Threshold | Status |
|--------|-------|-----------|--------|
| Recall@5 | 7.4% | 70% | FAIL |
| Recall@10 | 11.1% | 80% | FAIL |

**By Category:**
- Simple (n=7): 14.3% @5, 19.0% @10
- Medium (n=6): 5.6% @5, 5.6% @10
- Edge (n=5): 0.0% @5, 6.7% @10

**Analysis:** Low baseline recall indicates ground truth test cases may be too specific (exact verse matching) or the embedding search needs tuning. This provides a baseline for improvement.

## Tests Passing

All 66 existing API tests pass.

## Success Criteria

- [x] vLLM startup script created (requires manual server start)
- [x] Judge client implemented for Qwen2
- [x] All 5 rubrics have prompt templates
- [x] Golden test set has 20 Q&A pairs
- [x] Retrieval ground truth has 18 test cases
- [x] Recall measurement working
- [x] RAG endpoint implemented
- [x] Baseline metrics established

## Dependencies

- RTX 5090 with CUDA 12.8+
- vLLM installed
- Qwen2.5-7B-Instruct model
- Azure OpenAI for embeddings and generation

## Progress Log

- 2026-01-12: Started implementation
- 2026-01-12: Created evaluation infrastructure (judge, rubrics, config, runner)
- 2026-01-12: Created vLLM startup script
- 2026-01-12: Created 20 golden Q&A pairs
- 2026-01-12: Dispatched parallel agents for retrieval and ask endpoint
- 2026-01-12: Created 18 retrieval ground truth test cases
- 2026-01-12: Implemented recall measurement module
- 2026-01-12: Implemented /api/v1/ask endpoint with RAG
- 2026-01-12: Ran baseline retrieval evaluation
- 2026-01-12: Phase complete
