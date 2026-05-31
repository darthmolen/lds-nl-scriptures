# Phase: Spanish Translation of the Jesus Christ Extract (multi-pass, experimental)

**Date:** 2026-05-31
**Branch:** `claude/jesus-christ-extract-sBhMV`
**Status:** ✅ Complete — titles + notes translated and verified inline (verified=true); no harness built
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

### Passes 2–4 — verification (done INLINE; no harness built)
**Decision:** the translatable surface turned out to be tiny — **259 words / 135 unique terms**
(35 model titles + 26 editorial notes; the other 1,416 notes are verse pull-outs replaced from
the official ES scriptures). A full corpus-index + AI-judge + human-queue harness was
**disproportionate**, so verification was done inline in-session:

- **Per-word attestation** of every title/note against the ES corpora (scriptures + 23
  conference talks + CFM, ~63 MB). The 26 editorial notes were all clean. 4 titles were
  non-word model garbles (Hijodividino, Luzeverde, Exempelar, Foredeterminado); others were
  Anglicisms (antemortal) or wrong-sense (Asunción, Pruebas).
- **Parallel EN/ES conference sourcing** for disputed terms (align talks by `uri`, paragraphs
  by `num`): "His trial" → "Su juicio" (Rasband 2023) confirmed **Juicios de** and rejected
  *Pruebas*; "divine Son of God" → **Hijo de Dios**. Verified by reading the actual references
  under "Trials of" — all legal (Caiaphas/Pilate/Annas), none about the desert temptation.
- **Human decisions** (the user) on remaining calls: Hijo de Dios, Linaje de David,
  Apariciones tras la Resurrección.
- 11 corrections baked into `_TITLE_OVERRIDES` (documented with sources). Final extract:
  **no unattested-word titles remain**; `translation.verified = true`.

If this is later scaled to many TG topics (not just Jesus Christ), revisit building the
automated Pass 2/3 harness; for a single topic it was unnecessary.

## Success criteria

- [x] Pass 0 glossary generated; coverage reported (17/53 official GE names).
- [x] Pass 1 produces fully-Spanish titles/notes; extract re-emitted.
- [x] Verification done inline (per-word corpus attestation + parallel-conference sourcing)
      instead of a harness; 1,416 notes verse-grounded, 26 notes clean, 11 titles corrected.
- [x] Human decisions captured; `translation.verified = true`.
- [n/a] Automated Pass 2/3/4 harness — deferred; unnecessary for a single topic (259-word surface).

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
