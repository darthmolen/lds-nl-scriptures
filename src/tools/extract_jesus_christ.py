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

_VOLUME_TO_URLVOL = {v: k for k, v in _URLVOL_TO_VOLUME.items()}

# (url_volume, church_book_code) -> (volume_id, json_slug)  [English slugs]
_BOOKCODE_MAP: dict[tuple[str, str], tuple[str, str]] = {}
# (volume_id, json-book-key) -> church_book_code. Accepts BOTH the church code
# (Spanish JSON keys books this way) AND the English slug (English JSON), so the
# verse index resolves the same TG href in either language.
_SLUG_TO_CODE: dict[tuple[str, str], str] = {}
for _vol_id, _pairs in _VOLUME_BOOKS.items():
    _url_vol = _VOLUME_TO_URLVOL[_vol_id]
    for _code, _slug in _pairs:
        _BOOKCODE_MAP[(_url_vol, _code)] = (_vol_id, _slug)
        _SLUG_TO_CODE[(_vol_id, _code)] = _code
        _SLUG_TO_CODE[(_vol_id, _slug)] = _code


# ---------------------------------------------------------------------------
# 1. Fetch
#
# The TG "Jesus Christ" topic is split across sibling pages on the Church study
# site: the main entry (/scriptures/tg/jesus-christ) carries a narrative summary
# plus a nav index linking to ~53 sub-topic pages
# (/scriptures/tg/jesus-christ-atonement-through, ...). Each page is served by
# the same content API, so we drive that API per URI rather than scraping a
# rendered DOM. The ~2,200 references live across the main page + sub-pages.
# ---------------------------------------------------------------------------
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; scripture-search/1.0)"}
RATE_LIMIT_DELAY = 0.15  # seconds between API calls


def _cache_path(uri: str, api_lang: str) -> Path:
    slug = uri.rstrip("/").split("/")[-1]
    return RAW_TG_DIR / api_lang / f"{slug}.json"


def fetch_page(uri: str, lang: str = "en", use_cache: bool = False) -> dict:
    """Fetch (or load) a single content-API page envelope for `uri`, caching raw."""
    api_lang = LANG_API[lang]
    cache = _cache_path(uri, api_lang)
    if use_cache and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    resp = requests.get(CHURCH_API, params={"lang": api_lang, "uri": uri},
                        headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def discover_subtopic_uris(main_data: dict) -> list[str]:
    """From the main entry's nav index, return the sub-topic page URIs that fall
    *under* Jesus Christ (uri path begins /scriptures/tg/jesus-christ-...).

    The nav also lists "See also" cross-references to other headwords (Bread of
    Life, Godhead, ...); those are excluded by the prefix filter.
    """
    soup = BeautifulSoup(main_data.get("content", {}).get("body", ""), "html.parser")
    uris: list[str] = []
    for a in soup.select("nav.index a, nav a"):
        path = a.get("href", "").split("?")[0]
        # Anchors carry a /study prefix; the content-API uri param omits it.
        if path.startswith("/study/"):
            path = path[len("/study"):]
        if path.startswith("/scriptures/tg/jesus-christ-") and path not in uris:
            uris.append(path)
    return uris


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


def parse_page_refs(body_html: str) -> list[dict]:
    """Extract scripture references from a single TG page's body HTML, in order.

    Each sub-topic is its own page, so a page maps to one sub-topic's reference
    list. References are the scripture-path anchors; "See also" topic cross-links
    and the nav index (which point at /scriptures/tg/... not /study/scriptures/...)
    are excluded by the href-path filter. The text preceding each anchor's
    paragraph (e.g. "His birth is foretold,") is captured as an optional note.
    """
    soup = BeautifulSoup(body_html, "html.parser")
    refs: list[dict] = []
    seen: set[tuple] = set()
    for a in soup.find_all("a"):
        href = a.get("href", "")
        m = _HREF_PATH_RE.search(href)
        if not m:
            continue
        url_vol, book_code, ch = m.group(1), m.group(2), int(m.group(3))
        verses = _verses_from_href(href)
        key = (url_vol, book_code, ch, tuple(verses))
        if key in seen:
            continue
        seen.add(key)
        refs.append({
            "ref": a.get_text(" ", strip=True),
            "url_vol": url_vol,
            "book_code": book_code,
            "ch": ch,
            "verses": verses,
            "href": href.split("?")[0],
            "note": _ref_note(a),
        })
    return refs


def _ref_note(anchor) -> str:
    """The lead-in prose of the anchor's paragraph (TG summary phrasing), if any."""
    p = anchor.find_parent("p")
    if p is None:
        return ""
    first = p.find("a", href=_HREF_PATH_RE)
    if first is not anchor:
        return ""  # only annotate the first reference in a paragraph
    # text before the first scripture anchor, trimmed
    parts = []
    for node in p.children:
        if node is first:
            break
        parts.append(node.get_text(" ", strip=True) if hasattr(node, "get_text")
                     else str(node).strip())
    note = " ".join(t for t in parts if t).strip(" ,;:.")
    # Drop "See also …" cross-reference lead-ins (topic links, not a verse gloss).
    if re.match(r"(?i)^(see also|véase también|véase)\b", note):
        return ""
    return note if 0 < len(note) <= 120 else ""


def subtopic_title(meta_title: str) -> str:
    """Normalise a page's meta.title into a sub-topic short label.

    "Jesus Christ"                     -> "Summary"
    "Jesus Christ, Atonement through"  -> "Atonement through"
    """
    t = meta_title.strip()
    if t.lower() == "jesus christ":
        return "Summary"
    prefix = "Jesus Christ,"
    if t.startswith(prefix):
        return t[len(prefix):].strip()
    return t


# ---------------------------------------------------------------------------
# 3. Verse index (offline; uses existing scripture JSON)
# ---------------------------------------------------------------------------
class VerseIndex:
    """Loads scripture JSON once and resolves references to text + context."""

    def __init__(self, lang: str = "en"):
        self.lang = lang
        # (url_vol, church_book_code, chapter) -> list[str] verse texts (1-indexed)
        self._chapters: dict[tuple[str, str, int], list[str]] = {}
        # (url_vol, church_book_code) -> book title (in this language)
        self._titles: dict[tuple[str, str], str] = {}
        self._load()

    def _load(self) -> None:
        src = PROCESSED_DIR / self.lang
        for json_file in sorted(src.glob("*.json")):
            if json_file.name == "all_scriptures.json":
                continue
            data = json.loads(json_file.read_text(encoding="utf-8"))
            volume_id = json_file.stem  # e.g. "newtestament"
            url_vol = _VOLUME_TO_URLVOL.get(volume_id)
            if url_vol is None:
                continue
            for slug, book in data.get("books", {}).items():
                # JSON keys books by English slug (en) or church code (es); both
                # normalise to the church code so resolution is language-agnostic.
                code = _SLUG_TO_CODE.get((volume_id, slug))
                if code is None:
                    continue
                self._titles[(url_vol, code)] = book.get("title", slug)
                for ch_str, chapter in book.get("chapters", {}).items():
                    try:
                        ch = int(ch_str)
                    except ValueError:
                        continue  # e.g. D&C official declarations ("od1")
                    texts = [v.get("text", "") for v in chapter.get("verses", [])]
                    self._chapters[(url_vol, code, ch)] = texts

    def book_title(self, url_vol: str, book_code: str) -> str:
        return self._titles.get((url_vol, book_code), book_code)

    def chapter_len(self, url_vol: str, book_code: str, ch: int) -> int:
        return len(self._chapters.get((url_vol, book_code, ch), []))

    def verse_text(self, url_vol: str, book_code: str, ch: int, vs: int) -> Optional[str]:
        texts = self._chapters.get((url_vol, book_code, ch))
        if not texts or vs < 1 or vs > len(texts):
            return None
        return texts[vs - 1]

    def resolve(self, url_vol: str, book_code: str, ch: int,
                verses: Iterable[int]) -> Optional[dict]:
        """Resolve a reference to {book, ch, verses, context[]} or None if unknown."""
        n = self.chapter_len(url_vol, book_code, ch)
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
            {"vs": vs, "text": self.verse_text(url_vol, book_code, ch, vs) or "",
             "target": vs in target}
            for vs in range(lo, hi + 1)
        ]
        return {
            "vol": _URLVOL_TO_VOLUME.get(url_vol, url_vol),
            "book": book_code,
            "book_title": self.book_title(url_vol, book_code),
            "ch": ch,
            "verses": verses,
            "context": context,
        }


# ---------------------------------------------------------------------------
# 4. Build extract
# ---------------------------------------------------------------------------
def build_extract(parsed: list[dict], index: VerseIndex, lang: str = "en",
                  structure_lang: str = "en", relabel: bool = False) -> dict:
    """Assemble the extract.

    `parsed` (sub-topic structure + references) comes from the `structure_lang`
    TG pages; verse text/context come from `index` (the target `lang`). When
    `relabel` is True (cross-language build), reference labels are rebuilt from
    the target-language book titles ("Lucas 1:26–38") instead of reusing the
    structure-language anchor text. Sub-topic titles and summary notes stay in
    `structure_lang` until a separate translation pass fills them in.
    """
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
            label = _label(resolved) if relabel else (r["ref"] or _label(resolved))
            entry = {"ref": label, **resolved}
            if r.get("note"):
                entry["note"] = r["note"]
            refs_out.append(entry)
        if refs_out:
            short = st["short"]
            title = "Jesus Christ" if short in ("", "Summary") else f"Jesus Christ, {short}"
            out_subtopics.append({
                "title": title,
                "short": short,
                "references": refs_out,
            })

    cross_lang = structure_lang != lang
    return {
        "topic": "Jesus Christ",
        "language": lang,
        "source": {
            "name": "Topical Guide",
            "api": CHURCH_API,
            "uri": TG_URI,
            "structure_language": structure_lang,
            "text_language": lang,
        },
        # For a cross-language build, sub-topic titles and reference notes are
        # still in `structure_lang` and await a translation pass.
        "translation": {
            "titles_language": structure_lang,
            "notes_language": structure_lang,
            "pending": cross_lang,
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
def collect_pages(lang: str, use_cache: bool) -> list[dict]:
    """Fetch the main TG entry + every Jesus-Christ sub-topic page; parse each
    into {short, references}. The main page becomes the "Summary" sub-topic."""
    import time

    main_data = fetch_page(TG_URI, lang, use_cache=use_cache)
    pages = [(TG_URI, main_data)]
    sub_uris = discover_subtopic_uris(main_data)
    print(f"  discovered {len(sub_uris)} sub-topic pages")

    for uri in sub_uris:
        try:
            pages.append((uri, fetch_page(uri, lang, use_cache=use_cache)))
        except Exception as e:  # noqa: BLE001 - report and continue
            print(f"  WARN: failed to fetch {uri}: {e}", file=sys.stderr)
        if not use_cache:
            time.sleep(RATE_LIMIT_DELAY)

    parsed = []
    for uri, data in pages:
        body = data.get("content", {}).get("body", "")
        if not body:
            print(f"  WARN: empty body for {uri}", file=sys.stderr)
            continue
        short = subtopic_title(data.get("meta", {}).get("title", uri.split("/")[-1]))
        parsed.append({"short": short, "references": parse_page_refs(body)})
    return parsed


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build the Jesus Christ TG study extract.")
    ap.add_argument("--lang", default="en", choices=["en", "es"],
                    help="Language of the verse text in the output.")
    ap.add_argument("--structure-lang", default=None, choices=["en", "es"],
                    help="Language whose TG pages provide the sub-topic structure and "
                         "reference list (default: same as --lang). Use --structure-lang en "
                         "with --lang es to map the full English TG onto Spanish scriptures "
                         "(the Spanish GEE is far sparser). Titles/notes stay in this "
                         "language pending a translation pass.")
    ap.add_argument("--from-cache", action="store_true",
                    help="Reuse cached raw pages instead of fetching from the API.")
    args = ap.parse_args(argv)
    structure_lang = args.structure_lang or args.lang

    print(f"== Jesus Christ TG extract (text={args.lang}, structure={structure_lang}) ==")
    print("  collecting TG pages from Church content API...")
    parsed = collect_pages(structure_lang, use_cache=args.from_cache)
    if not parsed:
        print("ERROR: no TG pages parsed.", file=sys.stderr)
        return 1
    print(f"  parsed {len(parsed)} sub-topics, "
          f"{sum(len(s['references']) for s in parsed)} references (pre-resolve)")

    index = VerseIndex(args.lang)
    extract = build_extract(parsed, index, args.lang,
                            structure_lang=structure_lang,
                            relabel=(structure_lang != args.lang))
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
