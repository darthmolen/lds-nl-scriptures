# Scripture Search Project Roadmap

## Overview

Building a semantic scripture search system with RAG capabilities for English and Spanish LDS scriptures, Topical Guide, and Come Follow Me materials.

## Phases

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| 1 | Content Preparation | Convert PDFs to structured markdown | Planning |
| 2 | Data Ingestion | Parse markdown into database schema | Not Started |
| 3 | Embedding Generation | Generate embeddings with text-embedding-3-small | Not Started |
| 4 | Search API | Build semantic search with pgvector + FastAPI | Not Started |
| 5 | RAG Generation | Add gpt-4o-mini response generation | Not Started |
| 6 | Topical Guide | Integrate topical guide lookups | Not Started |
| 7 | Come Follow Me | Add CFM content as separate table | Not Started |

## Architecture Stack

- **Database**: PostgreSQL with pgvector extension
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)
- **Generation**: OpenAI gpt-4o-mini
- **API**: Python FastAPI
- **Auth**: Azure Entra ID (private for now)
- **Infrastructure**: Azure AKS (existing)

## Content Sources

| Content | Languages | Source Format |
|---------|-----------|---------------|
| Scriptures (Quad) | EN, ES | PDF → Markdown |
| Come Follow Me | EN, ES | PDF → Markdown |
| Topical Guide | EN | To be determined |

## Phase Details

- [PHASE01-CONTENT_PREPARATION.md](./PHASE01-CONTENT_PREPARATION.md) - PDF to Markdown conversion
- [PHASE02-DATA_INGESTION.md](./PHASE02-DATA_INGESTION.md) - Parse and load to database
- [PHASE03-EMBEDDINGS.md](./PHASE03-EMBEDDINGS.md) - Generate vector embeddings
- [PHASE04-SEARCH_API.md](./PHASE04-SEARCH_API.md) - Semantic search endpoints
- [PHASE05-RAG_GENERATION.md](./PHASE05-RAG_GENERATION.md) - Response generation with citations
- [PHASE06-TOPICAL_GUIDE.md](./PHASE06-TOPICAL_GUIDE.md) - Topical guide integration
- [PHASE07-COME_FOLLOW_ME.md](./PHASE07-COME_FOLLOW_ME.md) - CFM content integration
