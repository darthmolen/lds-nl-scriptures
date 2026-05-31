# Backlog: "Scriptures: Jesus The Christ" reading app(s)

**Date:** 2026-05-31
**Status:** 🌱 Rough sketch — pending a formal brainstorm session (do NOT implement yet)
**Home:** a NEW, separate repo (not `lds-nl-scriptures`; this repo is the data pipeline)

## Why (motivation)

Come Follow Me, May 25–31 2026 ("The Lord Raised Up a Deliverer," Judges 2–4; 6–8; 13–16)
points to Elder Neil L. Andersen's Oct 2020 general-conference talk *"We Talk of Christ."*
About the 6th paragraph in, it recounts President Russell M. Nelson's challenge (see that
talk's footnote 10 for where it was given) to study **all ~2,200 Topical Guide references
under "Jesus Christ."** President Nelson said he had taken the challenge himself and that **it
changed him** — a 92-year-old apostle of 50+ years, changed by it. (He has since passed away.)

The goal: let **anyone** read the words of and about Christ in that curated set and have their
lives changed — and lower the barrier for Christians who may be wary of the LDS faith.

## Vision: two store listings, ONE codebase, two data *scopes*

- **Scriptures: Jesus The Christ (Bible Only)** — references whose verses are in the Old/New
  Testament.
- **Scriptures: Jesus The Christ (Full)** — all standard works.

The separation is pastoral/outreach, not technical: "Bible Only" is simply a **filter** on the
data we already produced. Build as one app with two flavors / listings.

**Android first.** (iOS later.)

## Content is already built and portable

The data is the committed Topical Guide extract:

- `content/processed/scriptures/en/topical-guide/jesus-christ.json`
- `content/processed/scriptures/es/topical-guide/jesus-christ.json` (Spanish, verified)
- (TOON mirrors under `content/transformed/...` for token-efficient uses)

Each reference already carries: `vol` (`ot|nt|bofm|pgp|dc-testament`), `book`, `ch`, `verses`,
the **full verse text + ±2 verse context**, a `note` gloss, and sub-topic grouping.
→ **Bible Only = filter `vol ∈ {ot, nt}`.** Ship the JSON as a **bundled offline asset**:
no backend, no accounts, works anywhere.

## Core features (v1 — keep it simple, "Kindle-like")

- **Reading comfort:** adjustable font family + size; light/dark themes.
- **Reference cards:** each reference shown in its own demarcated block with the **reference
  title (e.g. "Lucas 1:26–38") on top**; verse text + ±2 context inside; target verses
  emphasized.
- **Slice & dice views:** browse all references, or organize by **book**, by **topic**
  (sub-topic), or **book + topic**.
- **Per-reference note button:** write and save personal thoughts.
- **Per-reference checkmark:** mark as read/studied.
- **Progress chart:** track completion toward the full set (the "challenge" tracker).

## Architecture sketch (to be confirmed in brainstorm)

- Android, offline-first; bundled JSON data asset.
- **On-device storage** for notes + checkmarks + progress (no login for v1) → private, free, simple.
- One codebase, two product flavors (Bible Only / Full); EN + ES content available.

## Explicitly out of scope for v1 (YAGNI)

- Accounts, cloud sync, social features.
- Notes backup/export (a *later* nicety).
- iOS (after Android proves the concept).
- Audio, search, study-plan scheduling (revisit later).

## Open questions for the formal brainstorm

1. Native Android (Kotlin/Compose) vs cross-platform (Flutter/KMP) — given iOS is a later goal.
2. On-device storage choice (e.g. Room/SQLite vs simple files) and the notes/progress data model.
3. **Licensing/attribution** per translation: KJV (EN) is public domain; the Spanish text and
   the Topical Guide *structure* are Church-copyright. This most affects the public-facing
   "Bible Only" outreach app — resolve before distribution.
4. Exact "challenge" progress model (per-reference vs per-sub-topic vs total %).
5. Navigation/IA for slice-and-dice and how notes/checkmarks surface across views.
6. Branding/naming, store presence, and how the two flavors are presented.

## Next step

Run a **formal brainstorm session** (superpowers:brainstorming) in the new app repo:
clarify the open questions → propose approaches → produce a design spec → hand to
writing-plans. This document is the seed for that session.
