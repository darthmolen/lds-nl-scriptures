"""Offline tests for the Jesus Christ TG extract pipeline.

These exercise everything except the network fetch, using the real scripture JSON
already in the repo plus a small synthetic TG-HTML fixture that mimics the Church
content-API structure.
"""

import json

import pytest

from src.tools.extract_jesus_christ import (
    _BOOKCODE_MAP,
    _VOLUME_BOOKS,
    PROCESSED_DIR,
    VerseIndex,
    build_extract,
    discover_subtopic_uris,
    flatten_for_toon,
    parse_page_refs,
    subtopic_title,
    _verses_from_href,
)


# --- href verse parsing -----------------------------------------------------
@pytest.mark.parametrize("href,expected", [
    ("/study/scriptures/nt/john/1?lang=eng&id=p1#p1", [1]),
    ("/study/scriptures/nt/john/1?lang=eng&id=p1-p3#p1", [1, 2, 3]),
    ("/study/scriptures/nt/matt/1?lang=eng&id=p18,p20#p18", [18, 20]),
    ("/study/scriptures/nt/john/1?lang=eng", []),
])
def test_verses_from_href(href, expected):
    assert _verses_from_href(href) == expected


# --- book-code map covers every JSON slug -----------------------------------
def test_bookcode_map_matches_json_slugs():
    mapped_slugs = {slug for (_v, slug) in _BOOKCODE_MAP.values()}
    for json_file in sorted((PROCESSED_DIR / "en").glob("*.json")):
        if json_file.name == "all_scriptures.json":
            continue
        data = json.loads(json_file.read_text(encoding="utf-8"))
        for slug in data.get("books", {}):
            assert slug in mapped_slugs, f"{slug} not in book-code map"


# --- VerseIndex resolution + context ----------------------------------------
@pytest.fixture(scope="module")
def index():
    return VerseIndex("en")


def test_resolve_single_verse_with_context(index):
    r = index.resolve("nt", "john", 1, [1])
    assert r["book"] == "john"
    assert r["verses"] == [1]
    # John 1:1 has no verses before it -> context starts at verse 1 (clamped).
    vs_nums = [c["vs"] for c in r["context"]]
    assert vs_nums == [1, 2, 3]  # 1 .. 1+2
    target = [c for c in r["context"] if c["target"]]
    assert [c["vs"] for c in target] == [1]
    assert r["context"][0]["text"].startswith("In the beginning was the Word")


def test_context_clamps_at_chapter_end(index):
    n = index.chapter_len("nt", "john", 1)
    r = index.resolve("nt", "john", 1, [n])  # last verse
    assert max(c["vs"] for c in r["context"]) == n  # not n+2


def test_resolve_range(index):
    r = index.resolve("nt", "john", 1, [1, 2, 3])
    assert r["verses"] == [1, 2, 3]
    assert min(c["vs"] for c in r["context"]) == 1
    assert max(c["vs"] for c in r["context"]) == 5  # 3 + 2


def test_resolve_unknown_returns_none(index):
    assert index.resolve("nt", "not-a-book", 1, [1]) is None
    assert index.resolve("nt", "john", 999, [1]) is None


def test_resolve_is_language_agnostic_spanish():
    """Spanish JSON keys books by church code; the same TG href must resolve."""
    es = VerseIndex("es")
    r = es.resolve("nt", "matt", 1, [1])  # church code "matt", same as English href
    assert r is not None
    assert r["book"] == "matt"
    assert r["context"][0]["text"]  # non-empty Spanish verse text
    # Book of Mormon hyphenated code and D&C section keying also resolve.
    assert es.resolve("bofm", "1-ne", 1, [1]) is not None
    assert es.resolve("dc-testament", "dc", 19, [1]) is not None


# --- HTML parse + build + TOON flatten --------------------------------------
# The main TG entry: a nav index (sub-topic links + "See also" cross-refs) plus a
# narrative summary whose paragraphs lead with prose before the scripture links.
MAIN_HTML = """
<header><h1>Jesus Christ</h1></header>
<div class="body-block">
  <nav class="index"><ul class="reference">
    <li><a href="/study/scriptures/tg/godhead?lang=eng">Godhead</a></li>
    <li><a href="/study/scriptures/tg/jesus-christ-antemortal-existence-of?lang=eng">Jesus Christ, Antemortal Existence of</a></li>
    <li><a href="/study/scriptures/tg/jesus-christ-creator?lang=eng">Jesus Christ, Creator</a></li>
  </ul></nav>
  <p>His birth is foretold,
     <a href="/study/scriptures/nt/luke/1?lang=eng&id=p26-p38#p26">Luke 1:26-38</a>.</p>
  <p>is born,
     <a href="/study/scriptures/nt/matt/1?lang=eng&id=p18-p25#p18">Matt. 1:18-25</a>
     (<a href="/study/scriptures/nt/luke/2?lang=eng&id=p1-p7#p1">Luke 2:1-7</a>).</p>
</div>
"""

# A sub-topic page body: title comes from meta.title, refs are scripture anchors.
SUBTOPIC_HTML = """
<div class="body-block">
  <p><a href="/study/scriptures/nt/john/1?lang=eng&id=p1-p3#p1">John 1:1-3</a>.
     See also <a href="/study/scriptures/tg/creation?lang=eng">TG Creation</a>.</p>
</div>
"""


def test_subtopic_title_normalisation():
    assert subtopic_title("Jesus Christ") == "Summary"
    assert subtopic_title("Jesus Christ, Atonement through") == "Atonement through"
    assert subtopic_title("Jesus Christ, Creator") == "Creator"


def test_discover_subtopic_uris_filters_to_jesus_christ():
    uris = discover_subtopic_uris({"content": {"body": MAIN_HTML}})
    assert "/scriptures/tg/jesus-christ-antemortal-existence-of" in uris
    assert "/scriptures/tg/jesus-christ-creator" in uris
    # "See also Godhead" is a different headword -> excluded.
    assert all("godhead" not in u for u in uris)


def test_parse_page_refs_extracts_scripture_anchors_only():
    refs = parse_page_refs(SUBTOPIC_HTML)
    assert len(refs) == 1  # the TG Creation cross-link is excluded
    assert refs[0]["verses"] == [1, 2, 3]
    assert refs[0]["book_code"] == "john"


def test_parse_page_refs_captures_summary_note():
    refs = parse_page_refs(MAIN_HTML)
    # Nav-index links are /scriptures/tg/... so excluded; only the 3 scripture refs remain.
    assert len(refs) == 3
    luke = next(r for r in refs if r["ref"].startswith("Luke 1"))
    assert luke["note"] == "His birth is foretold"


def test_build_and_flatten(index):
    parsed = [
        {"short": "Summary", "references": parse_page_refs(MAIN_HTML)},
        {"short": "Creator", "references": parse_page_refs(SUBTOPIC_HTML)},
    ]
    extract = build_extract(parsed, index, "en")
    assert extract["topic"] == "Jesus Christ"
    assert extract["stats"]["resolved"] == extract["stats"]["references"]
    titles = [st["title"] for st in extract["subtopics"]]
    assert "Jesus Christ" in titles  # the summary page
    assert "Jesus Christ, Creator" in titles

    rows = flatten_for_toon(extract)
    assert rows, "expected flattened TOON rows"
    row = rows[0]
    assert set(row) >= {"subtopic", "ref", "vol", "book", "ch", "vs", "text", "context"}
    assert any("*" in r["context"] for r in rows)  # target verses marked in context

    # TOON serialisation round-trips through the library if present.
    toons = pytest.importorskip("toons")
    assert toons.dumps(rows)


def test_cross_language_build_relabels_and_flags_translation():
    """English structure + Spanish text: labels rebuilt in Spanish, titles/notes
    flagged as awaiting translation."""
    es = VerseIndex("es")
    parsed = [{"short": "Summary", "references": parse_page_refs(MAIN_HTML)}]
    extract = build_extract(parsed, es, lang="es", structure_lang="en", relabel=True)
    assert extract["language"] == "es"
    assert extract["translation"]["pending"] is True
    assert extract["translation"]["titles_language"] == "en"
    assert extract["stats"]["unresolved"] == 0
    ref = extract["subtopics"][0]["references"][0]
    # Label rebuilt from the Spanish book title (e.g. "Lucas"), not the English anchor.
    assert ref["ref"].startswith("Lucas")
    assert ref["context"][0]["text"]  # Spanish verse text present
