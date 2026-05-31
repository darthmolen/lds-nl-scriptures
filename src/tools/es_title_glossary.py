#!/usr/bin/env python3
"""Pass 0 of the Spanish translation: build a sub-topic title glossary by mapping
each TG "Jesus Christ" sub-topic to its official Spanish name in the Guía para el
Estudio de las Escrituras (GEE), where one exists.

Deterministic, no model. Output seeds Pass 1 (model translation) so only the
sub-topics WITHOUT an official GE headword need the model.

Usage:
    python src/tools/es_title_glossary.py            # fetch GE manifest live
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root on path

from src.tools.extract_jesus_christ import (
    PROJECT_ROOT, RAW_TG_DIR, CHURCH_API, _HEADERS, subtopic_title,
)

OUT = PROJECT_ROOT / "content" / "transformed" / "scriptures" / "es" / "topical-guide"
GE_MANIFEST_URI = "/scriptures/gs/jesucristo"  # returns the full A-Z GE manifest

# High-confidence aliases where the TG sub-topic slug differs from the GE headword
# slug. Kept small and explicit; everything else falls through to the model (Pass 1)
# and is verified in Pass 3.
_GE_SLUG_ALIASES = {
    "atonement-through": "atone-atonement",
    "death-of": "death-physical",
    "taking-the-name-of": "name",
}


def fetch_ge_name_map() -> dict[str, str]:
    """{ge_topic_slug: official_spanish_name} from the GE manifest."""
    r = requests.get(CHURCH_API, params={"lang": "spa", "uri": GE_MANIFEST_URI},
                     headers=_HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.json()["content"]["body"], "html.parser")
    out: dict[str, str] = {}
    for a in soup.find_all("a"):
        href = a.get("href", "").split("?")[0]
        if href.startswith("/study/scriptures/gs/"):
            out[href.rsplit("/", 1)[-1]] = a.get_text(" ", strip=True)
    return out


def tg_subtopic_slugs() -> list[tuple[str, str]]:
    """[(tg_slug, english_short)] from the cached EN sub-topic raw pages."""
    pages = sorted((RAW_TG_DIR / "eng").glob("jesus-christ-*.json"))
    rows = []
    for p in pages:
        data = json.loads(p.read_text(encoding="utf-8"))
        short = subtopic_title(data.get("meta", {}).get("title", p.stem))
        rows.append((p.stem, short))
    return rows


def build_glossary() -> dict:
    ge = fetch_ge_name_map()
    entries = []
    covered = 0
    for tg_slug, short in tg_subtopic_slugs():
        bare = re.sub(r"^jesus-christ-", "", tg_slug)
        ge_slug = bare if bare in ge else _GE_SLUG_ALIASES.get(bare)
        official = ge.get(ge_slug) if ge_slug else None
        if official:
            covered += 1
        entries.append({
            "english_short": short,
            "tg_slug": tg_slug,
            "ge_slug": ge_slug,
            "official_es": official,
            "needs_model": official is None,
        })
    return {
        "topic": "Jesus Christ",
        "ge_topics_indexed": len(ge),
        "subtopics": len(entries),
        "official_coverage": covered,
        "needs_model": len(entries) - covered,
        "entries": entries,
    }


def main() -> int:
    g = build_glossary()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "jesus-christ.title-glossary.json"
    path.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"GE topics indexed: {g['ge_topics_indexed']}")
    print(f"sub-topics: {g['subtopics']}  | official GE name: {g['official_coverage']}"
          f"  | need model: {g['needs_model']}")
    print("  official examples:")
    for e in g["entries"]:
        if e["official_es"]:
            print(f"    {e['english_short']:32} -> {e['official_es']}")
    print("  need model:", [e["english_short"] for e in g["entries"] if e["needs_model"]])
    print(f"wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
