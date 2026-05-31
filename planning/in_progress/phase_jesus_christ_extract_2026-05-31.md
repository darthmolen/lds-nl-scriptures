# Phase: Jesus Christ Topical Guide Extract

**Date:** 2026-05-31
**Branch:** `claude/jesus-christ-extract-sBhMV`
**Status:** In progress (offline scaffolding complete; live TG fetch gated on network allowlist)

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

- [ ] Live fetch of the TG "Jesus Christ" entry succeeds and is cached to `content/raw/tg/`.
- [ ] Parser extracts sub-topics + references (target: in the low ~2,000s of references).
- [ ] ≥99% of references resolve to verse text in the existing JSON (unresolved are reported).
- [ ] Each reference carries full verse text + ±2 context, clamped to chapter bounds.
- [x] Resolver + context + TOON emit validated offline against real scripture JSON (pytest).
- [ ] JSON + TOON outputs written; token-savings stat reported.

## Resume instructions (for the session after allowlist is live)

1. Confirm reachability:
   `python -c "import requests;print(requests.get('https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content',params={'lang':'eng','uri':'/scriptures/tg/jesus-christ'},timeout=30).status_code)"`
   — expect `200`.
2. Run: `python src/tools/extract_jesus_christ.py --lang en`
3. Inspect printed stats + a few sample entries; eyeball `content/raw/tg/jesus-christ.eng.json`
   to confirm the HTML parse matched the real structure (the parser is the only part that
   could not be validated offline).
4. Run tests: `pytest tests/test_jesus_christ_extract.py -q`
5. Commit outputs; move this doc to `planning/completed/`.

## Deviations / notes

- (to be filled in after live run)
