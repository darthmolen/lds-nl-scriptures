# LDS Scripture Search

A semantic search system for LDS scriptures and Come Follow Me content, supporting English and Spanish.

## Project Goal

Build a RAG (Retrieval-Augmented Generation) system that enables natural language queries across:

- All five standard works (Old Testament, New Testament, Book of Mormon, Doctrine & Covenants, Pearl of Great Price)
- Come Follow Me lesson content (2023-2026)
- Cross-references and footnotes

## Architecture

- **Database**: PostgreSQL with pgvector for vector similarity search
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Generation**: GPT-4o-mini for answer synthesis
- **API**: Python FastAPI
- **Auth**: Azure Entra ID (private deployment)

## Data Sources

### Scriptures

**English scriptures** are sourced from the [Open Scripture API](https://openscriptureapi.org/), an open-source project providing structured access to LDS scriptures with:

- Full verse text
- Footnotes with character positions
- Chapter summaries
- Cross-references

**Spanish scriptures** and **Come Follow Me content** are sourced from [The Church of Jesus Christ of Latter-day Saints](https://www.churchofjesuschrist.org/) website's public content API.

### Attribution

This project uses data from:

- **Open Scripture API** ([openscriptureapi.org](https://openscriptureapi.org/)) - English scriptures with footnotes
- **The Church of Jesus Christ of Latter-day Saints** ([churchofjesuschrist.org](https://www.churchofjesuschrist.org/)) - Spanish scriptures and Come Follow Me content

Scripture text is copyrighted by Intellectual Reserve, Inc. This project is for personal/educational use.

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Content Preparation | Complete |
| 2 | Data Ingestion | Planned |
| 3 | Embeddings | Planned |
| 4 | Search API | Planned |
| 5 | RAG Generation | Planned |
| 6 | Topical Guide | Planned |
| 7 | Come Follow Me | Planned |

### Phase 1 Results

- **English**: 41,995 verses with footnotes
- **Spanish**: 41,996 verses with footnotes
- **Come Follow Me**: 4 years × 2 languages (208 lessons)
- **Format**: JSON (source) + TOON (token-optimized, 23.6% reduction)

## Repository Structure

```
lds-nl-scriptures/
├── content/
│   ├── processed/          # JSON from APIs
│   │   ├── scriptures/{en,es}/
│   │   └── cfm/{en,es}/
│   └── transformed/        # TOON format for LLM context
│       ├── scriptures/{en,es}/
│       └── cfm/{en,es}/
├── src/
│   └── tools/              # Data extraction scripts
│       ├── fetch_scriptures.py
│       ├── fetch_cfm.py
│       └── convert_to_toon.py
├── planning/               # Phase documentation
│   ├── completed/
│   └── roadmap.md
└── documentation/
    └── TOON-FORMAT-SUMMARY.md
```

## Quick Start

### Fetch Scripture Data

```bash
# Install dependencies
pip install requests beautifulsoup4

# Fetch all scriptures (EN + ES)
python src/tools/fetch_scriptures.py --lang both

# Fetch Come Follow Me (specific year)
python src/tools/fetch_cfm.py --year 2026 --lang both
```

### Convert to TOON Format

```bash
# Install TOON library
pip install toons tiktoken

# Convert to token-optimized format
python src/tools/convert_to_toon.py --type all
```

## TOON Format

[TOON (Token-Oriented Object Notation)](https://toonformat.dev/) reduces LLM token usage by 30-60% for tabular data. Scripture verses convert well due to their uniform structure:

```
[6604]{book,ch,vs,text,fn}:
  1nephi,1,1,"I, Nephi, having been born of goodly parents...","22:26:TG Birthright.|30:36:Prov. 22:1."
  1nephi,1,2,"Yea, I make a record in the language of my father...","28:36:Mosiah 1:4; Morm. 9:32."
```

See [TOON-FORMAT-SUMMARY.md](documentation/TOON-FORMAT-SUMMARY.md) for details.

## License

Code in this repository is MIT licensed. Scripture content is copyrighted by Intellectual Reserve, Inc. and used under fair use for personal/educational purposes.
