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
    flatten_for_toon,
    parse_tg_html,
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
    n = index.chapter_len("newtestament", "john", 1)
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


# --- HTML parse + build + TOON flatten --------------------------------------
SAMPLE_HTML = """
<div class="body-block">
  <p><strong>Jesus Christ.</strong> See also God.</p>
  <p><em>Antemortal Existence of.</em>
     <a href="/study/scriptures/nt/john/1?lang=eng&id=p1#p1">John 1:1</a>,
     <a href="/study/scriptures/nt/john/1?lang=eng&id=p2#p2">2</a>.</p>
  <p><em>Creator.</em>
     <a href="/study/scriptures/nt/john/1?lang=eng&id=p1-p3#p1">John 1:1-3</a>.
     See also <a href="/study/scriptures/tg/creation?lang=eng">TG Creation</a>.</p>
</div>
"""


def test_parse_tg_html_groups_subtopics():
    parsed = parse_tg_html(SAMPLE_HTML)
    shorts = [s["short"] for s in parsed]
    assert "Antemortal Existence of" in shorts
    assert "Creator" in shorts
    creator = next(s for s in parsed if s["short"] == "Creator")
    # The "See also TG Creation" link is not a scripture href -> excluded.
    assert len(creator["references"]) == 1
    assert creator["references"][0]["verses"] == [1, 2, 3]


def test_build_and_flatten(index):
    parsed = parse_tg_html(SAMPLE_HTML)
    extract = build_extract(parsed, index, "en")
    assert extract["topic"] == "Jesus Christ"
    assert extract["stats"]["resolved"] == extract["stats"]["references"]
    # Titles are namespaced under "Jesus Christ, ..."
    assert any(st["title"].startswith("Jesus Christ,") for st in extract["subtopics"])

    rows = flatten_for_toon(extract)
    assert rows, "expected flattened TOON rows"
    row = rows[0]
    assert set(row) >= {"subtopic", "ref", "vol", "book", "ch", "vs", "text", "context"}
    assert "[1]*" in row["context"]  # target verse marked in context blob

    # TOON serialisation round-trips through the library if present.
    toons = pytest.importorskip("toons")
    assert toons.dumps(rows)
