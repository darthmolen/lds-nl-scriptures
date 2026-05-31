# Phase: Spanish Translation of the Jesus Christ Extract (multi-pass, experimental)

**Date:** 2026-05-31
**Branch:** `claude/jesus-christ-extract-sBhMV`
**Status:** Pass 0 ✅ · Pass 1 ✅ (draft; several titles garbled — Pass 3 will verify) · Pass 2–4 pending
**Depends on:** completed EN/ES v1 extract (`planning/completed/phase_jesus_christ_extract_2026-05-31.md`)

## Objective

Translate the **English placeholder strings** in the Spanish Jesus Christ extract
(`content/processed/scriptures/es/topical-guide/jesus-christ.json`) — **53 sub-topic titles +
~103 summary notes** — into doctrinally faithful Spanish, then verify each rendering against
**official Church parallel corpora** rather than trusting raw model output.

Verse text and reference labels are already correct Spanish; only `title`/`note` fields and the
`translation.pending` flag change.

## Guiding principle (user's design)

Don't trust a single model translation for doctrinal terms. Translate, then **cross-reference
every key term against approved sources**, use **AI-as-judge** to adjudicate mismatches, and
escalate ties to a **human decider**. Build it in passes; treat it as an experiment.

## Available parallel corpora (already in repo)

- EN/ES scriptures — `content/processed/scriptures/{en,es}/` (verse-aligned by ref).
- EN/ES general conference — `content/processed/conference/{en,es}/` (prophets & leaders).
- CFM (Come Follow Me) — `content/processed/cfm/` (church-correlated).
- GEE official topic names — `/scriptures/gs/*` (official Spanish headwords).

## Passes

### Pass 0 — Title glossary from the GEE (deterministic, no model)
- Map each of the 53 TG sub-topics to a GE headword by slug (strip `jesus-christ-` →
  look up in the GE manifest `{slug: es_name}`).
- Output a reviewable glossary: `english_short`, `tg_slug`, `ge_slug`, `official_es | null`,
  `needs_model`. Report coverage (how many of 53 get official names).
- Artifact: `content/transformed/scriptures/es/topical-guide/jesus-christ.title-glossary.json`.

### Pass 1 — Direct model translation (v1)
- Model: **Qwen2.5-14B-Instruct** via the local vLLM OpenAI-compatible API
  (`src/evaluation/llm_local/start.sh`; `http://localhost:8004/v1`).
- Seed titles with Pass-0 official names; model-translate only the `needs_model` titles + all
  ~103 notes. Few-shot with a small built-in LDS glossary + the official names as exemplars.
- Write translated `title`/`note` back; keep `translation.pending = true` (still unverified).
- Re-emit JSON + TOON.

### Pass 2 — Attested-term index (deterministic)
- For each key term/phrase, mine EN→ES renderings actually attested in the corpora:
  - scripture: align by reference (we have both languages per verse);
  - conference/CFM: align by talk/lesson + paragraph where feasible.
- Output: `term → {attested_es_renderings: [...], sources: [...], counts}`.

### Pass 3 — AI-as-judge verification
- For every translated term, check membership in its attested set. If absent or low-frequency,
  the judge (same local model, separate rubric) scores candidate renderings against context and
  flags a mismatch with a confidence score.
- Output: a verification report with per-term verdicts (confirmed / corrected / disputed).

### Pass 4 — Human tie-break
- Disputed/low-confidence/tie cases queue to a human-review file; decisions fold back in and
  set `translation.pending = false` once cleared.

## Success criteria

- [ ] Pass 0 glossary generated; coverage reported.
- [ ] Pass 1 produces fully-Spanish titles/notes; extract re-emitted.
- [ ] Pass 2 term index built from ≥2 corpora.
- [ ] Pass 3 judge report; mismatches flagged with confidence.
- [ ] Pass 4 human-review queue; pending flag cleared after resolution.

## Notes / decisions

- Model fixed at Qwen2.5-14B-Instruct (5090, unquantized) for translation **and** judge.
- No EnglishConnect glossary (it's a language course, not a terminology source) — its
  per-section *principios* are not a term bank.
- `_ASYNC_`: Pass 2 corpus mining is independent of Pass 1 and can run in parallel.

## Prerequisite to start Pass 1

Start the local model, then signal:
```
JUDGE_LLM_MODEL=Qwen/Qwen2.5-14B-Instruct src/evaluation/llm_local/start.sh
# verify: curl -s http://localhost:8004/v1/models
```
