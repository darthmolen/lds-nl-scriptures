# Phase: Jesus Christ Topical Guide Extract

**Date:** 2026-05-31
**Branch:** `claude/jesus-christ-extract-sBhMV`
**Status:** ✅ EN complete (2,196 refs, 53 sub-topics, 0 unresolved) · 🟡 ES v1 complete,
title/note translation pending

## Objective

Create a self-contained **"Jesus Christ" study extract** containing the scriptures listed
under the Topical Guide entry *Jesus Christ* (and its sub-topics), with **full verse text +
±2 verse context**, so a downstream study application can use it without re-extracting.

## Approach (decided with user)

- **Source of references:** the *actual* Topical Guide "Jesus Christ" entry (forward list),
  **not** the footnote reverse-index.
  - Decision rationale: the footnote reverse-index in our existing JSON yields only ~863
    verses / 991 TG-Jesus-Christ sub-topic occurrences — a *selective subset* of the real TG
    entry. The published TG "Jesus Christ" entry lists ~2,200 references.
- **Source system:** the Church content API
  `https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content`
  with `uri=/scriptures/tg/jesus-christ` — the same source family already used for the Spanish
  scriptures (`src/tools/fetch_scriptures.py`).
- **Content per reference:** reference label, volume/book/chapter/verse(s), full verse text,
  and ±2 verse context window (matches the architecture's "verse-level chunks with ±2 verse
  context").
- **Outputs:**
  - JSON: `content/processed/scriptures/en/topical-guide/jesus-christ.json`
  - TOON: `content/transformed/scriptures/en/topical-guide/jesus-christ.toon`
  - Raw API cache (reproducibility): `content/raw/tg/jesus-christ.eng.json`

## Key technical facts discovered

- Footnotes in the scripture JSON use a **non-breaking space**: `TG\xa0Jesus Christ, ...`.
- Church book URL codes (from `SPANISH_BOOKS` in `fetch_scriptures.py`) align **in canonical
  order, 1:1** with our JSON book slugs per volume, so the code map is built by zipping:
  - OT: `gen→genesis`, `ex→exodus`, … (39 books)
  - NT: `matt→matthew`, … (27)
  - BoM: `1-ne→1nephi`, `w-of-m→wordsofmormon`, `hel→helaman`, … (15)
  - PGP: `moses→moses`, `abr→abraham`, `js-m→josephsmithmatthew`, … (5)
  - D&C: `dc→doctrineandcovenants` (chapters keyed by section number)
- `toons` + `tiktoken` are in `requirements.txt` (PyPI reachable; install in setup).

## Blocker / prerequisite

The Church/OpenScripture hosts are **not in this environment's network allowlist**
("Host not in allowlist"). The user is adding `churchofjesuschrist.org` /
`www.churchofjesuschrist.org` to the environment network policy. The proxy is configured at
session start, so the extraction's **fetch step runs on the next session** after the allowlist
is live.

## Files to add / modify

- `src/tools/extract_jesus_christ.py` — main pipeline (fetch → parse → resolve → emit).
- `tests/test_jesus_christ_extract.py` — offline tests for the resolver, context window, and
  TOON emit using the real scripture JSON already in the repo.
- Outputs (generated on live run): the JSON/TOON/raw-cache files listed above.

## Success criteria

- [x] Live fetch of the TG "Jesus Christ" entry succeeds and is cached to `content/raw/tg/`.
- [x] Parser extracts sub-topics + references (**2,196 refs / 53 sub-topics** — matches the
      article's ~2,200).
- [x] 100% of references resolve to verse text in the existing JSON (**0 unresolved**).
- [x] Each reference carries full verse text + ±2 context, clamped to chapter bounds.
- [x] Resolver + context + TOON emit validated offline against real scripture JSON (pytest, 14 tests).
- [x] JSON + TOON outputs written; token-savings stat reported (TOON ~9.9% smaller).

## How it ran (final)

- Run locally (teleported session) after `git merge origin/main` (PR #6) — Church API reachable
  from the local machine, so no allowlist change was needed.
- Command: `python src/tools/extract_jesus_christ.py --lang en`
- Outputs:
  - `content/processed/scriptures/en/topical-guide/jesus-christ.json` (3.7 MB)
  - `content/transformed/scriptures/en/topical-guide/jesus-christ.toon` (2.5 MB, 2,196 rows)
  - `content/raw/tg/eng/*.json` (53 cached pages, 840 KB) — enables `--from-cache` offline rebuilds.

## Deviations / notes

- **Major structural finding:** the TG "Jesus Christ" topic is NOT one page. The main entry
  (`/scriptures/tg/jesus-christ`) holds a 103-ref narrative *Summary* plus a nav index linking
  to **52 separate sub-topic pages** (`/scriptures/tg/jesus-christ-atonement-through`, …). The
  ~2,200 references are spread across main + sub-pages.
- The first design parsed a single page and grouped sub-topics by leading emphasized text — it
  found only 1 bucket / 104 refs. **Reworked** to: discover sub-topic URIs from the main page's
  nav (filtered to the `/scriptures/tg/jesus-christ-` prefix; "See also" cross-headwords like
  Godhead/Bread of Life excluded), fetch each via the same content API, and treat **one page =
  one sub-topic** (`parse_page_refs` + `subtopic_title`).
- "Underlying API" = `/study/api/v3/language-pages/type/content?uri=…` (already used for the
  Spanish scriptures). It returns a JSON envelope with `content.body` HTML; references are the
  `/study/scriptures/<vol>/<book>/<ch>?id=pN-pM` anchors. `content.footnotes` is empty for TG
  topic pages, and `pids` are just paragraph asset IDs — no structured ref list, so anchors are
  the source of truth.
- Nav hrefs carry a `/study` prefix; the content-API `uri` param omits it (normalised in
  `discover_subtopic_uris`).
- Summary-page references also capture the TG narrative lead-in as a `note`
  (e.g. "His birth is foretold").

## Spanish extract (English TG structure → Spanish scriptures)

Spanish has **no Topical Guide**; the non-English analogue is the *Guía para el Estudio de las
Escrituras* (GEE). The GEE "Jesucristo" entry (`/scriptures/gs/jesus-christ?lang=spa`, cached
to `content/raw/gee/spa/jesus-christ.json`) is **far sparser**: **287 references, flat, no
sub-topics** — ~13% of the TG. (Note: the GE uses English slugs; `/gs/jesucristo` returns the
whole A-Z manifest, the real entry is `/gs/jesus-christ`.)

**Decision:** skip the GEE; map the full **English TG structure onto Spanish scripture text**.
TG references are language-independent church codes (`nt/matt/1`), and `VerseIndex` is
language-agnostic (resolves either English slugs or the church codes that the Spanish JSON uses
as book keys), so:

- Command: `python src/tools/extract_jesus_christ.py --lang es --structure-lang en --from-cache`
- Result: **2,196 / 2,196 resolved, 0 unresolved**, 53 sub-topics, full Spanish verse text.
- Reference labels rebuilt from Spanish book titles ("Lucas 1:26–38", "Levítico 17:11").
- Outputs: `content/processed/scriptures/es/topical-guide/jesus-christ.json` +
  `content/transformed/scriptures/es/topical-guide/jesus-christ.toon`.

**v1 limitation (pending translation):** sub-topic titles ("Jesus Christ, Atonement through")
and summary notes ("His birth is foretold") remain **English placeholders**. Flagged in the
output as `translation.pending = true` with `titles_language/notes_language = "en"`. Scope to
translate ≈ **53 titles + ~103 notes**. Plan: translate via the local vLLM
(`src/evaluation/llm_local/start.sh`, OpenAI-compatible at `http://localhost:8004/v1`,
Qwen2.5-7B/14B-Instruct) in a follow-up pass and re-emit.

## Follow-ups (backlog candidates)

- **ES title/note translation pass** (next): fill the ~156 English placeholder strings via the
  local model; set `translation.pending = false`.
- Optionally include the 5 "See also" cross-reference topics (Bread of Life, Cornerstone,
  God Creator, Godhead, God the Father Jehovah) if the study app wants them.
