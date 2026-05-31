#!/usr/bin/env python3
"""Build the "Jesus Christ" Topical Guide study extract.

Pipeline:
  1. fetch_tg_entry()    -- pull the real TG "Jesus Christ" entry from the Church
                            content API (forward reference list, NOT the footnote
                            reverse-index). Cached to content/raw/tg/.
  2. parse_tg_html()     -- extract sub-topics + scripture references from the HTML.
  3. VerseIndex          -- load existing scripture JSON once; resolve references to
                            full verse text + a +/-2 verse context window.
  4. build_extract()     -- assemble the self-contained study JSON.
  5. write_outputs()     -- emit JSON + token-efficient TOON.

Only step 1 needs network. Steps 2-5 are exercised offline by
tests/test_jesus_christ_extract.py against the scripture JSON already in the repo.

Usage:
    python src/tools/extract_jesus_christ.py --lang en
    python src/tools/extract_jesus_christ.py --lang en --from-cache   # reuse raw cache
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "content" / "processed" / "scriptures"
TRANSFORMED_DIR = PROJECT_ROOT / "content" / "transformed" / "scriptures"
RAW_TG_DIR = PROJECT_ROOT / "content" / "raw" / "tg"

CHURCH_API = "https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content"
TG_URI = "/scriptures/tg/jesus-christ"

LANG_API = {"en": "eng", "es": "spa"}

# Context window: +/- this many verses around the referenced verse(s).
CONTEXT_RADIUS = 2

# ---------------------------------------------------------------------------
# Church scripture-URL book codes -> our JSON (volume, book-slug).
#
# The code lists below are in canonical scripture order and align 1:1 with the
# book slugs in content/processed/scriptures/en/*.json, so the map is built by
# zipping. (Codes sourced from SPANISH_BOOKS in fetch_scriptures.py.)
# ---------------------------------------------------------------------------
_VOLUME_BOOKS: dict[str, list[tuple[str, str]]] = {
    # volume_id : [(church_code, json_slug), ...]
    "oldtestament": [
        ("gen", "genesis"), ("ex", "exodus"), ("lev", "leviticus"), ("num", "numbers"),
        ("deut", "deuteronomy"), ("josh", "joshua"), ("judg", "judges"), ("ruth", "ruth"),
        ("1-sam", "1samuel"), ("2-sam", "2samuel"), ("1-kgs", "1kings"), ("2-kgs", "2kings"),
        ("1-chr", "1chronicles"), ("2-chr", "2chronicles"), ("ezra", "ezra"),
        ("neh", "nehemiah"), ("esth", "esther"), ("job", "job"), ("ps", "psalms"),
        ("prov", "proverbs"), ("eccl", "ecclesiastes"), ("song", "songofsolomon"),
        ("isa", "isaiah"), ("jer", "jeremiah"), ("lam", "lamentations"), ("ezek", "ezekiel"),
        ("dan", "daniel"), ("hosea", "hosea"), ("joel", "joel"), ("amos", "amos"),
        ("obad", "obadiah"), ("jonah", "jonah"), ("micah", "micah"), ("nahum", "nahum"),
        ("hab", "habakkuk"), ("zeph", "zephaniah"), ("hag", "haggai"), ("zech", "zechariah"),
        ("mal", "malachi"),
    ],
    "newtestament": [
        ("matt", "matthew"), ("mark", "mark"), ("luke", "luke"), ("john", "john"),
        ("acts", "acts"), ("rom", "romans"), ("1-cor", "1corinthians"),
        ("2-cor", "2corinthians"), ("gal", "galatians"), ("eph", "ephesians"),
        ("philip", "philippians"), ("col", "colossians"), ("1-thes", "1thessalonians"),
        ("2-thes", "2thessalonians"), ("1-tim", "1timothy"), ("2-tim", "2timothy"),
        ("titus", "titus"), ("philem", "philemon"), ("heb", "hebrews"), ("james", "james"),
        ("1-pet", "1peter"), ("2-pet", "2peter"), ("1-jn", "1john"), ("2-jn", "2john"),
        ("3-jn", "3john"), ("jude", "jude"), ("rev", "revelation"),
    ],
    "bookofmormon": [
        ("1-ne", "1nephi"), ("2-ne", "2nephi"), ("jacob", "jacob"), ("enos", "enos"),
        ("jarom", "jarom"), ("omni", "omni"), ("w-of-m", "wordsofmormon"),
        ("mosiah", "mosiah"), ("alma", "alma"), ("hel", "helaman"), ("3-ne", "3nephi"),
        ("4-ne", "4nephi"), ("morm", "mormon"), ("ether", "ether"), ("moro", "moroni"),
    ],
    "pearlofgreatprice": [
        ("moses", "moses"), ("abr", "abraham"), ("js-m", "josephsmithmatthew"),
        ("js-h", "josephsmithhistory"), ("a-of-f", "articlesoffaith"),
    ],
    # D&C uses sections rather than books; the church URL book code is "dc".
    "doctrineandcovenants": [("dc", "doctrineandcovenants")],
}

# church URL volume segment -> our volume_id / file stem
_URLVOL_TO_VOLUME = {
    "ot": "oldtestament",
    "nt": "newtestament",
    "bofm": "bookofmormon",
    "pgp": "pearlofgreatprice",
    "dc-testament": "doctrineandcovenants",
}

# (url_volume, church_book_code) -> (volume_id, json_slug)
_BOOKCODE_MAP: dict[tuple[str, str], tuple[str, str]] = {}
for _vol_id, _pairs in _VOLUME_BOOKS.items():
    _url_vol = {v: k for k, v in _URLVOL_TO_VOLUME.items()}[_vol_id]
    for _code, _slug in _pairs:
        _BOOKCODE_MAP[(_url_vol, _code)] = (_vol_id, _slug)


# ---------------------------------------------------------------------------
# 1. Fetch
# ---------------------------------------------------------------------------
def fetch_tg_entry(lang: str = "en") -> dict:
    """Fetch the raw TG 'Jesus Christ' content-API envelope and cache it."""
    api_lang = LANG_API[lang]
    params = {"lang": api_lang, "uri": TG_URI}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; scripture-search/1.0)"}
    resp = requests.get(CHURCH_API, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    RAW_TG_DIR.mkdir(parents=True, exist_ok=True)
    cache = RAW_TG_DIR / f"jesus-christ.{api_lang}.json"
    cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  cached raw TG entry -> {cache.relative_to(PROJECT_ROOT)}")
    return data


def load_cached_entry(lang: str = "en") -> dict:
    cache = RAW_TG_DIR / f"jesus-christ.{LANG_API[lang]}.json"
    return json.loads(cache.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 2. Parse
# ---------------------------------------------------------------------------
# Scripture anchor href: /study/scriptures/<urlvol>/<book>/<chapter>?...id=pX[-pY][,pZ]...
_HREF_PATH_RE = re.compile(r"/study/scriptures/([a-z0-9-]+)/([a-z0-9-]+)/(\d+)")
_ID_TOKEN_RE = re.compile(r"p(\d+)")


def _verses_from_href(href: str) -> list[int]:
    """Parse verse numbers from the ?id=p..-p.. fragment of a scripture href."""
    verses: list[int] = []
    m = re.search(r"[?&]id=([^&#]+)", href)
    if not m:
        return verses
    for chunk in m.group(1).split(","):
        nums = _ID_TOKEN_RE.findall(chunk)
        if len(nums) == 1:
            verses.append(int(nums[0]))
        elif len(nums) >= 2:
            verses.extend(range(int(nums[0]), int(nums[1]) + 1))
    return sorted(dict.fromkeys(verses))


def parse_tg_html(body_html: str) -> list[dict]:
    """Parse the TG 'Jesus Christ' body HTML into sub-topics with references.

    Returns: [{"short": <subtopic title>, "references": [
                 {"ref": <label>, "url_vol", "book_code", "ch", "verses", "href"}]}]

    Grouping heuristic: the TG entry is a sequence of paragraphs; a paragraph that
    opens with an emphasized phrase (<em>/<i>/<b>/<strong>) before its first
    scripture link starts a new sub-topic. Scripture links are recognised by their
    href path, so "See also" topic cross-links (which point at other TG entries,
    not /study/scriptures/...) are naturally excluded.
    """
    soup = BeautifulSoup(body_html, "html.parser")
    subtopics: list[dict] = []
    current: Optional[dict] = None

    paragraphs = soup.find_all("p")
    if not paragraphs:  # fall back to the whole document as one block
        paragraphs = [soup]

    for p in paragraphs:
        anchors = [a for a in p.find_all("a") if _HREF_PATH_RE.search(a.get("href", ""))]

        # Detect a sub-topic title: leading emphasized text before the first scripture link.
        title = None
        lead = p.find(["em", "i", "b", "strong"])
        if lead is not None:
            lead_text = lead.get_text(" ", strip=True).strip(" .,:")
            # A title is short-ish prose, not itself a scripture link, and must appear
            # before the paragraph's first scripture reference.
            if lead_text and lead not in anchors:
                first_anchor = anchors[0] if anchors else None
                if first_anchor is None or _precedes_in(p, lead, first_anchor):
                    title = lead_text

        if title is not None:
            current = {"short": title, "references": []}
            subtopics.append(current)

        if not anchors:
            continue
        if current is None:  # references before any heading -> generic bucket
            current = {"short": "", "references": []}
            subtopics.append(current)

        for a in anchors:
            href = a.get("href", "")
            m = _HREF_PATH_RE.search(href)
            if not m:
                continue
            url_vol, book_code, ch = m.group(1), m.group(2), int(m.group(3))
            verses = _verses_from_href(href)
            current["references"].append({
                "ref": a.get_text(" ", strip=True),
                "url_vol": url_vol,
                "book_code": book_code,
                "ch": ch,
                "verses": verses,
                "href": href,
            })

    # Drop empty buckets.
    return [s for s in subtopics if s["references"]]


def _precedes_in(parent, a, b) -> bool:
    """True if element `a` appears before `b` within `parent` (document order)."""
    for el in parent.descendants:
        if el is a:
            return True
        if el is b:
            return False
    return True


# ---------------------------------------------------------------------------
# 3. Verse index (offline; uses existing scripture JSON)
# ---------------------------------------------------------------------------
class VerseIndex:
    """Loads scripture JSON once and resolves references to text + context."""

    def __init__(self, lang: str = "en"):
        self.lang = lang
        # (volume_id, slug, chapter) -> list[str] verse texts (1-indexed -> idx 0)
        self._chapters: dict[tuple[str, str, int], list[str]] = {}
        # slug -> book title
        self._titles: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        src = PROCESSED_DIR / self.lang
        for json_file in sorted(src.glob("*.json")):
            if json_file.name == "all_scriptures.json":
                continue
            data = json.loads(json_file.read_text(encoding="utf-8"))
            volume_id = json_file.stem  # e.g. "newtestament"
            for slug, book in data.get("books", {}).items():
                self._titles[slug] = book.get("title", slug)
                for ch_str, chapter in book.get("chapters", {}).items():
                    try:
                        ch = int(ch_str)
                    except ValueError:
                        continue  # e.g. D&C official declarations ("od1")
                    texts = [v.get("text", "") for v in chapter.get("verses", [])]
                    self._chapters[(volume_id, slug, ch)] = texts

    def book_title(self, slug: str) -> str:
        return self._titles.get(slug, slug)

    def chapter_len(self, volume_id: str, slug: str, ch: int) -> int:
        return len(self._chapters.get((volume_id, slug, ch), []))

    def verse_text(self, volume_id: str, slug: str, ch: int, vs: int) -> Optional[str]:
        texts = self._chapters.get((volume_id, slug, ch))
        if not texts or vs < 1 or vs > len(texts):
            return None
        return texts[vs - 1]

    def resolve(self, url_vol: str, book_code: str, ch: int,
                verses: Iterable[int]) -> Optional[dict]:
        """Resolve a reference to {book, ch, verses, context[]} or None if unknown."""
        mapped = _BOOKCODE_MAP.get((url_vol, book_code))
        if mapped is None:
            return None
        volume_id, slug = mapped
        n = self.chapter_len(volume_id, slug, ch)
        if n == 0:
            return None
        verses = sorted({v for v in verses if 1 <= v <= n})
        if not verses:
            # whole-chapter reference -> treat all verses as targets
            verses = list(range(1, n + 1))
        lo = max(1, min(verses) - CONTEXT_RADIUS)
        hi = min(n, max(verses) + CONTEXT_RADIUS)
        target = set(verses)
        context = [
            {"vs": vs, "text": self.verse_text(volume_id, slug, ch, vs) or "",
             "target": vs in target}
            for vs in range(lo, hi + 1)
        ]
        return {
            "vol": volume_id,
            "book": slug,
            "book_title": self.book_title(slug),
            "ch": ch,
            "verses": verses,
            "context": context,
        }


# ---------------------------------------------------------------------------
# 4. Build extract
# ---------------------------------------------------------------------------
def build_extract(parsed: list[dict], index: VerseIndex, lang: str = "en") -> dict:
    out_subtopics = []
    n_refs = n_unresolved = 0
    unresolved_samples: list[str] = []

    for st in parsed:
        refs_out = []
        for r in st["references"]:
            n_refs += 1
            resolved = index.resolve(r["url_vol"], r["book_code"], r["ch"], r["verses"])
            if resolved is None:
                n_unresolved += 1
                if len(unresolved_samples) < 25:
                    unresolved_samples.append(r["ref"] or r["href"])
                continue
            refs_out.append({"ref": r["ref"] or _label(resolved), **resolved})
        if refs_out:
            short = st["short"]
            out_subtopics.append({
                "title": f"Jesus Christ, {short}" if short else "Jesus Christ",
                "short": short,
                "references": refs_out,
            })

    return {
        "topic": "Jesus Christ",
        "language": lang,
        "source": {
            "name": "Topical Guide",
            "api": CHURCH_API,
            "uri": TG_URI,
        },
        "context_radius": CONTEXT_RADIUS,
        "generated": date.today().isoformat(),
        "stats": {
            "subtopics": len(out_subtopics),
            "references": n_refs,
            "resolved": n_refs - n_unresolved,
            "unresolved": n_unresolved,
            "unresolved_samples": unresolved_samples,
        },
        "subtopics": out_subtopics,
    }


def _label(resolved: dict) -> str:
    vs = resolved["verses"]
    rng = f"{vs[0]}" if len(vs) == 1 else f"{vs[0]}–{vs[-1]}"
    return f"{resolved['book_title']} {resolved['ch']}:{rng}"


# ---------------------------------------------------------------------------
# 5. Outputs (JSON + TOON)
# ---------------------------------------------------------------------------
def flatten_for_toon(extract: dict) -> list[dict]:
    """One TOON row per reference; context inlined as a compact, study-ready blob."""
    rows = []
    for st in extract["subtopics"]:
        for r in st["references"]:
            vs = r["verses"]
            context_blob = " ".join(
                f"[{c['vs']}]{'*' if c['target'] else ''} {c['text']}"
                for c in r["context"]
            )
            target_text = " ".join(
                c["text"] for c in r["context"] if c["target"]
            )
            rows.append({
                "subtopic": st["short"],
                "ref": r["ref"],
                "vol": r["vol"],
                "book": r["book"],
                "ch": r["ch"],
                "vs": vs[0] if len(vs) == 1 else f"{vs[0]}-{vs[-1]}",
                "text": target_text,
                "context": context_blob,
            })
    return rows


def write_outputs(extract: dict, lang: str = "en") -> dict:
    json_dir = PROCESSED_DIR / lang / "topical-guide"
    toon_dir = TRANSFORMED_DIR / lang / "topical-guide"
    json_dir.mkdir(parents=True, exist_ok=True)
    toon_dir.mkdir(parents=True, exist_ok=True)

    json_path = json_dir / "jesus-christ.json"
    json_path.write_text(json.dumps(extract, ensure_ascii=False, indent=2), encoding="utf-8")

    toon_path = toon_dir / "jesus-christ.toon"
    toon_info = {}
    try:
        import toons
        rows = flatten_for_toon(extract)
        toon_str = toons.dumps(rows)
        toon_path.write_text(toon_str, encoding="utf-8")
        toon_info = {"toon": str(toon_path.relative_to(PROJECT_ROOT)), "rows": len(rows)}
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            json_rows = json.dumps(flatten_for_toon(extract), ensure_ascii=False)
            jt, tt = len(enc.encode(json_rows)), len(enc.encode(toon_str))
            toon_info["savings_pct"] = round((1 - tt / jt) * 100, 1) if jt else 0
        except Exception:
            pass
    except Exception as e:  # toons not installed -> JSON is still the source of truth
        toon_info = {"toon": None, "warning": f"TOON skipped: {e}"}

    return {"json": str(json_path.relative_to(PROJECT_ROOT)), **toon_info}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Jesus Christ TG study extract.")
    ap.add_argument("--lang", default="en", choices=["en", "es"])
    ap.add_argument("--from-cache", action="store_true",
                    help="Reuse the cached raw TG entry instead of fetching.")
    args = ap.parse_args(argv)

    print(f"== Jesus Christ TG extract ({args.lang}) ==")
    if args.from_cache:
        print("  loading cached raw TG entry...")
        data = load_cached_entry(args.lang)
    else:
        print("  fetching TG entry from Church content API...")
        data = fetch_tg_entry(args.lang)

    body = data.get("content", {}).get("body", "")
    if not body:
        print("ERROR: empty content body in TG response.", file=sys.stderr)
        return 1

    parsed = parse_tg_html(body)
    print(f"  parsed {len(parsed)} sub-topics, "
          f"{sum(len(s['references']) for s in parsed)} references")

    index = VerseIndex(args.lang)
    extract = build_extract(parsed, index, args.lang)
    s = extract["stats"]
    print(f"  resolved {s['resolved']}/{s['references']} references "
          f"({s['unresolved']} unresolved) across {s['subtopics']} sub-topics")
    if s["unresolved_samples"]:
        print(f"  unresolved samples: {s['unresolved_samples'][:8]}")

    info = write_outputs(extract, args.lang)
    print(f"  wrote {info}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
