#!/usr/bin/env python3
"""Pass 1 of the Spanish translation: translate the English placeholder titles and
summary notes in the Spanish Jesus Christ extract using the local vLLM model.

- Sub-topic titles: seeded with official GEE Spanish names (Pass 0 glossary);
  only the remainder are model-translated.
- Summary notes: all model-translated.
- Verse text + reference labels are already Spanish and are left untouched.

Translations are cached to a sidecar JSON for traceability and to make re-runs
free; Pass 3 (corpus verification) reads the same file. This pass sets
translation.translated = true, verified = false (still unverified).

Prereq: local vLLM serving an OpenAI-compatible API (default http://localhost:8004/v1).
    JUDGE_LLM_MODEL=Qwen/Qwen2.5-14B-Instruct-AWQ src/evaluation/llm_local/start.sh --quantized

Usage:
    python src/tools/translate_jesus_christ_es.py
    python src/tools/translate_jesus_christ_es.py --dry-run   # show plan, no calls
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.tools.extract_jesus_christ import (  # noqa: E402
    PROJECT_ROOT, VerseIndex, _VOLUME_TO_URLVOL, write_outputs,
)


def _norm(s: str) -> str:
    s = s.replace("…", " ").replace("...", " ")
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def is_verse_pullout(note: str, en_text: str) -> bool:
    """True if every substantive piece of `note` (split on ellipses) appears
    verbatim in the English verse text — i.e. the note is a direct scripture quote
    rather than an editorial summary phrase."""
    vt = _norm(en_text)
    if not vt:
        return False
    pieces = [p for p in re.split(r"…|\.\.\.", note) if len(_norm(p).split()) >= 2]
    return all(_norm(p) in vt for p in (pieces or [note]))


def _es_target_text(ref: dict) -> str:
    return " ".join(c["text"] for c in ref["context"] if c.get("target"))

ES_DIR = PROJECT_ROOT / "content" / "processed" / "scriptures" / "es" / "topical-guide"
GLOSSARY = (PROJECT_ROOT / "content" / "transformed" / "scriptures" / "es"
            / "topical-guide" / "jesus-christ.title-glossary.json")
CACHE = ES_DIR.parent.parent.parent.parent / "transformed" / "scriptures" / "es" \
    / "topical-guide" / "jesus-christ.translations.json"

LLM_URL = os.getenv("JUDGE_LLM_URL", "http://localhost:8004/v1")

# Hard-coded, unambiguous renderings (avoid burning a model call / risking drift).
_BUILTIN = {"Summary": "Resumen"}

# Few-shot terminology anchors (official GE names) for the title prompt.
_TITLE_FEWSHOT = [
    ("Advocate", "Abogado"), ("Atonement through", "Expiación"),
    ("Creator", "Creador"), ("Redeemer", "Redentor"), ("Savior", "Salvador"),
    ("Lamb of God", "Cordero de Dios"), ("Only Begotten Son", "Unigénito"),
    ("Second Coming", "Segunda Venida"),
]

TITLE_SYS = (
    "Eres traductor experto en las Escrituras y la doctrina de La Iglesia de "
    "Jesucristo de los Santos de los Últimos Días. Traduce encabezados de subtemas "
    "de la Guía de Temas (Topical Guide) sobre Jesucristo a la terminología oficial "
    "de la Iglesia en español. Devuelve SOLO la traducción del encabezado, sin "
    "comillas, sin el prefijo «Jesucristo», sin explicación."
)
NOTE_SYS = (
    "Eres traductor experto en las Escrituras de La Iglesia de Jesucristo de los "
    "Santos de los Últimos Días. Traduce esta frase breve de un resumen de la vida "
    "de Jesucristo a un español natural y reverente, como en los materiales de la "
    "Iglesia. Devuelve SOLO la traducción, sin comillas ni explicación."
)


def _client():
    from openai import OpenAI
    client = OpenAI(base_url=LLM_URL, api_key="EMPTY")
    model = client.models.list().data[0].id
    return client, model


def _translate(client, model, system, text, fewshot=None) -> str:
    messages = [{"role": "system", "content": system}]
    for en, es in (fewshot or []):
        messages.append({"role": "user", "content": en})
        messages.append({"role": "assistant", "content": es})
    messages.append({"role": "user", "content": text})
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=0, max_tokens=64,
    )
    out = resp.choices[0].message.content.strip().strip('"').strip("«»").rstrip(".")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pass 1: translate ES titles + notes.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    extract = json.loads((ES_DIR / "jesus-christ.json").read_text(encoding="utf-8"))
    glossary = json.loads(GLOSSARY.read_text(encoding="utf-8"))
    official = {e["english_short"]: e["official_es"]
                for e in glossary["entries"] if e["official_es"]}

    # Classify notes: direct verse pull-outs are replaced from the Spanish
    # scriptures (authoritative, no model); only editorial notes go to the model.
    en_index = VerseIndex("en")
    n_pullout = 0
    notes_for_model: set[str] = set()
    for st in extract["subtopics"]:
        for r in st["references"]:
            note = r.get("note")
            if not note:
                continue
            uv = _VOLUME_TO_URLVOL.get(r["vol"])
            en_text = " ".join(en_index.verse_text(uv, r["book"], r["ch"], vs) or ""
                               for vs in r["verses"])
            if is_verse_pullout(note, en_text):
                r["_pullout"] = True
                n_pullout += 1
            else:
                notes_for_model.add(note)

    title_en = [st["short"] for st in extract["subtopics"]]
    titles_for_model = [t for t in title_en
                        if t not in _BUILTIN and t not in official]

    print(f"sub-topics: {len(title_en)}  | official: {len(set(title_en) & set(official))}"
          f"  | builtin: {len(set(title_en) & set(_BUILTIN))}"
          f"  | model titles: {len(titles_for_model)}")
    print(f"notes: {n_pullout} verse pull-outs (replaced from ES scriptures)  | "
          f"{len(notes_for_model)} editorial -> model")
    print(f"total model calls: {len(titles_for_model) + len(notes_for_model)}")
    if args.dry_run:
        print("titles -> model:", titles_for_model)
        print("editorial notes -> model:", sorted(notes_for_model))
        return 0

    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    t_cache = cache.get("titles", {})
    n_cache = cache.get("notes", {})

    client, model = _client()
    print(f"connected to {LLM_URL} | model: {model}")

    # Titles: builtin + official first, then model for the rest.
    title_es = {}
    for en in title_en:
        if en in _BUILTIN:
            title_es[en] = _BUILTIN[en]
        elif en in official:
            title_es[en] = official[en]
        elif en in t_cache:
            title_es[en] = t_cache[en]
        else:
            es = _translate(client, model, TITLE_SYS, en, _TITLE_FEWSHOT)
            title_es[en] = t_cache[en] = es
            print(f"  title  {en:34} -> {es}")

    # Editorial notes (non-pull-outs) only.
    note_es = {}
    model_notes = sorted(notes_for_model)
    for i, en in enumerate(model_notes, 1):
        if en in n_cache:
            note_es[en] = n_cache[en]
        else:
            es = _translate(client, model, NOTE_SYS, en)
            note_es[en] = n_cache[en] = es
            print(f"  note [{i}/{len(model_notes)}] {en[:42]!r} -> {es}")

    # Persist cache.
    CACHE.write_text(json.dumps(
        {"model": model, "generated": date.today().isoformat(),
         "titles": t_cache, "notes": n_cache}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    # Apply to the extract.
    for st in extract["subtopics"]:
        en = st["short"]
        es = title_es[en]
        st["short_en"] = en
        st["short"] = es
        st["title"] = "Jesucristo" if en in ("", "Summary") else f"Jesucristo, {es}"
        for r in st["references"]:
            note = r.pop("note", None)
            if not note:
                continue
            r["note_en"] = note
            if r.pop("_pullout", False):
                # Direct scripture quote -> official Spanish verse text.
                r["note"] = _es_target_text(r)
                r["note_source"] = "verse"
            else:
                r["note"] = note_es.get(note, note)
                r["note_source"] = "model"

    extract["translation"] = {
        "titles_language": "es", "notes_language": "es",
        "translated": True, "verified": False,
        "model": model,
        "official_seeded": len(set(title_en) & set(official)),
        "notes_from_verse": n_pullout, "notes_from_model": len(model_notes),
    }

    info = write_outputs(extract, "es")
    print(f"wrote {info}")
    print(f"cached translations -> {CACHE.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
