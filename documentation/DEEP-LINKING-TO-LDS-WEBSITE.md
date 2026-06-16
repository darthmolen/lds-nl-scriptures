# Deep-Linking to the Church (LDS) Website

How to build a stable URL that links a scripture reference directly to its verse on
[churchofjesuschrist.org](https://www.churchofjesuschrist.org/), with the verse(s)
highlighted and scrolled into view.

> This is **link construction only** — no API call, no scraping. The study-site URL
> scheme is predictable, so a reference can be turned into a URL with a simple lookup.
> (For the content-fetching API used elsewhere in this project, see the data-source
> notes in `README.md` and `planning/completed/PHASE01-CONTENT_PREPARATION.md`.)

## URL formula

```
https://www.churchofjesuschrist.org/study/scriptures/{volume}/{book}/{chapter}?lang={eng|spa}&id=p{verse}#p{verse}
```

| Part | Meaning |
|------|---------|
| `{volume}` | Volume code (see table below) |
| `{book}` | Book code (see table below) |
| `{chapter}` | Chapter number (for D&C this is the **section** number) |
| `lang` | `eng` (English) or `spa` (Spanish) — same URL shape for both |
| `id=` | Highlights the verse(s). Single: `p16` · range: `p7-p8` · list: `p7,p9,p11` |
| `#p{verse}` | Fragment that scrolls to the verse. Optional, but nice for UX |

Both `id=` and the `#p…` fragment are optional. Omit them to link to the whole chapter.

## Volume codes

| Volume | code |
|--------|------|
| Old Testament | `ot` |
| New Testament | `nt` |
| Book of Mormon | `bofm` |
| Doctrine & Covenants | `dc-testament` |
| Pearl of Great Price | `pgp` |

## Book codes

The book segment is the **church code** (the short form), not the full English slug.

### Old Testament (`ot`)

`gen` `ex` `lev` `num` `deut` `josh` `judg` `ruth` `1-sam` `2-sam` `1-kgs` `2-kgs`
`1-chr` `2-chr` `ezra` `neh` `esth` `job` `ps` `prov` `eccl` `song` `isa` `jer`
`lam` `ezek` `dan` `hosea` `joel` `amos` `obad` `jonah` `micah` `nahum` `hab`
`zeph` `hag` `zech` `mal`

### New Testament (`nt`)

`matt` `mark` `luke` `john` `acts` `rom` `1-cor` `2-cor` `gal` `eph` `philip` `col`
`1-thes` `2-thes` `1-tim` `2-tim` `titus` `philem` `heb` `james` `1-pet` `2-pet`
`1-jn` `2-jn` `3-jn` `jude` `rev`

### Book of Mormon (`bofm`)

`1-ne` `2-ne` `jacob` `enos` `jarom` `omni` `w-of-m` `mosiah` `alma` `hel` `3-ne`
`4-ne` `morm` `ether` `moro`

### Pearl of Great Price (`pgp`)

`moses` `abr` `js-m` `js-h` `a-of-f`

### Doctrine & Covenants (`dc-testament`)

Uses **sections**, not books. The book segment is literally `dc`, and the "chapter"
is the section number. Official Declarations use `od`.

> The authoritative, machine-readable version of these mappings lives in the codebase at
> [`src/tools/extract_jesus_christ.py`](../src/tools/extract_jesus_christ.py)
> (`_VOLUME_BOOKS`: `volume_id -> [(church_code, json_slug)]`; `_URLVOL_TO_VOLUME`: `url_volume -> volume_id`),
> with the Spanish book titles in [`src/tools/fetch_scriptures.py`](../src/tools/fetch_scriptures.py) (`SPANISH_BOOKS`).

## Gotchas

1. **D&C is section-based.** `dc-testament/dc/{section}` — e.g. D&C 121 →
   `.../dc-testament/dc/121`. Official Declarations: `.../dc-testament/od/1`.
2. **A few slugs aren't the obvious abbreviation.** Moroni is `moro`, Words of Mormon
   is `w-of-m`, Song of Solomon is `song`, JS—History is `js-h`, JS—Matthew is `js-m`,
   Articles of Faith is `a-of-f`. Pull exact codes from the map above rather than guessing.
3. **English vs. Spanish is only the `lang` param.** The volume/book/chapter path is
   identical across languages — you do not translate the book code.

## Examples

| Reference | URL |
|-----------|-----|
| John 3:16 | `https://www.churchofjesuschrist.org/study/scriptures/nt/john/3?lang=eng&id=p16#p16` |
| 1 Nephi 3:7 | `https://www.churchofjesuschrist.org/study/scriptures/bofm/1-ne/3?lang=eng&id=p7#p7` |
| Alma 32:21 (Spanish) | `https://www.churchofjesuschrist.org/study/scriptures/bofm/alma/32?lang=spa&id=p21#p21` |
| Moses 1:39 | `https://www.churchofjesuschrist.org/study/scriptures/pgp/moses/1?lang=eng&id=p39#p39` |
| D&C 121:7–8 (range) | `https://www.churchofjesuschrist.org/study/scriptures/dc-testament/dc/121?lang=eng&id=p7-p8#p7` |
| Helaman 5:12 | `https://www.churchofjesuschrist.org/study/scriptures/bofm/hel/5?lang=eng&id=p12#p12` |

## Reusable snippet

Drop-in helper for building links in another project. The `BOOK_CODES` table is the
same data as `_VOLUME_BOOKS` in this repo, inverted to map a friendly book name to
its `(volume, code)` pair.

```python
"""Build churchofjesuschrist.org deep links from a scripture reference."""

# friendly name (lowercased) -> (volume code, book code)
BOOK_CODES = {
    # Old Testament
    "genesis": ("ot", "gen"), "exodus": ("ot", "ex"), "leviticus": ("ot", "lev"),
    "numbers": ("ot", "num"), "deuteronomy": ("ot", "deut"), "joshua": ("ot", "josh"),
    "judges": ("ot", "judg"), "ruth": ("ot", "ruth"), "1 samuel": ("ot", "1-sam"),
    "2 samuel": ("ot", "2-sam"), "1 kings": ("ot", "1-kgs"), "2 kings": ("ot", "2-kgs"),
    "1 chronicles": ("ot", "1-chr"), "2 chronicles": ("ot", "2-chr"), "ezra": ("ot", "ezra"),
    "nehemiah": ("ot", "neh"), "esther": ("ot", "esth"), "job": ("ot", "job"),
    "psalms": ("ot", "ps"), "proverbs": ("ot", "prov"), "ecclesiastes": ("ot", "eccl"),
    "song of solomon": ("ot", "song"), "isaiah": ("ot", "isa"), "jeremiah": ("ot", "jer"),
    "lamentations": ("ot", "lam"), "ezekiel": ("ot", "ezek"), "daniel": ("ot", "dan"),
    "hosea": ("ot", "hosea"), "joel": ("ot", "joel"), "amos": ("ot", "amos"),
    "obadiah": ("ot", "obad"), "jonah": ("ot", "jonah"), "micah": ("ot", "micah"),
    "nahum": ("ot", "nahum"), "habakkuk": ("ot", "hab"), "zephaniah": ("ot", "zeph"),
    "haggai": ("ot", "hag"), "zechariah": ("ot", "zech"), "malachi": ("ot", "mal"),
    # New Testament
    "matthew": ("nt", "matt"), "mark": ("nt", "mark"), "luke": ("nt", "luke"),
    "john": ("nt", "john"), "acts": ("nt", "acts"), "romans": ("nt", "rom"),
    "1 corinthians": ("nt", "1-cor"), "2 corinthians": ("nt", "2-cor"),
    "galatians": ("nt", "gal"), "ephesians": ("nt", "eph"), "philippians": ("nt", "philip"),
    "colossians": ("nt", "col"), "1 thessalonians": ("nt", "1-thes"),
    "2 thessalonians": ("nt", "2-thes"), "1 timothy": ("nt", "1-tim"),
    "2 timothy": ("nt", "2-tim"), "titus": ("nt", "titus"), "philemon": ("nt", "philem"),
    "hebrews": ("nt", "heb"), "james": ("nt", "james"), "1 peter": ("nt", "1-pet"),
    "2 peter": ("nt", "2-pet"), "1 john": ("nt", "1-jn"), "2 john": ("nt", "2-jn"),
    "3 john": ("nt", "3-jn"), "jude": ("nt", "jude"), "revelation": ("nt", "rev"),
    # Book of Mormon
    "1 nephi": ("bofm", "1-ne"), "2 nephi": ("bofm", "2-ne"), "jacob": ("bofm", "jacob"),
    "enos": ("bofm", "enos"), "jarom": ("bofm", "jarom"), "omni": ("bofm", "omni"),
    "words of mormon": ("bofm", "w-of-m"), "mosiah": ("bofm", "mosiah"),
    "alma": ("bofm", "alma"), "helaman": ("bofm", "hel"), "3 nephi": ("bofm", "3-ne"),
    "4 nephi": ("bofm", "4-ne"), "mormon": ("bofm", "morm"), "ether": ("bofm", "ether"),
    "moroni": ("bofm", "moro"),
    # Doctrine & Covenants (section-based; book segment is "dc"; Official Declarations use "od")
    "doctrine and covenants": ("dc-testament", "dc"), "d&c": ("dc-testament", "dc"),
    "official declaration": ("dc-testament", "od"), "od": ("dc-testament", "od"),
    # Pearl of Great Price
    "moses": ("pgp", "moses"), "abraham": ("pgp", "abr"),
    "joseph smith—matthew": ("pgp", "js-m"), "joseph smith-matthew": ("pgp", "js-m"),
    "joseph smith—history": ("pgp", "js-h"), "joseph smith-history": ("pgp", "js-h"),
    "articles of faith": ("pgp", "a-of-f"),
}

BASE = "https://www.churchofjesuschrist.org/study/scriptures"


def scripture_url(book, chapter, verse=None, lang="eng"):
    """Build a churchofjesuschrist.org deep link for a scripture reference.

    Args:
        book:    Friendly book name, e.g. "John", "1 Nephi", "D&C" (case-insensitive).
        chapter: Chapter number (for D&C, the section number).
        verse:   Optional. An int (16), a (start, end) tuple for a range (7, 8),
                 or a list of ints for discrete verses [7, 9, 11].
        lang:    "eng" or "spa".

    Returns:
        Full URL string.

    Raises:
        KeyError: if the book name is not recognized.
        ValueError: if `verse` is an empty list/set or an invalid range tuple.
    """
    volume, code = BOOK_CODES[book.strip().lower()]
    url = f"{BASE}/{volume}/{code}/{chapter}?lang={lang}"

    if verse is None:
        return url

    if isinstance(verse, tuple):  # range, e.g. (7, 8) -> p7-p8
        if len(verse) != 2:
            raise ValueError("verse range must be a (start, end) tuple")
        start, end = verse
        ids = f"p{start}-p{end}"
        anchor = f"p{start}"
    elif isinstance(verse, (list, set)):  # discrete, e.g. [7, 9] -> p7,p9
        nums = sorted(verse)
        if not nums:
            raise ValueError("verse list must be non-empty")
        ids = ",".join(f"p{v}" for v in nums)
        anchor = f"p{nums[0]}"
    else:  # single int
        ids = anchor = f"p{verse}"

    return f"{url}&id={ids}#{anchor}"


if __name__ == "__main__":
    print(scripture_url("John", 3, 16))
    print(scripture_url("1 Nephi", 3, 7))
    print(scripture_url("Alma", 32, 21, lang="spa"))
    print(scripture_url("D&C", 121, (7, 8)))
    print(scripture_url("Moses", 1, 39))
```
