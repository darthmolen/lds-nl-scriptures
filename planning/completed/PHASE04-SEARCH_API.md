# Phase 4: Search API

## Objective

Build FastAPI endpoints for semantic scripture search.

## High-Level Tasks

1. **API Framework Setup**
   - Initialize FastAPI project structure
   - Configure database connections
   - Set up Azure Entra ID authentication

2. **Search Endpoint**
   - Accept natural language query
   - Embed query with text-embedding-3-small
   - Query pgvector for top-k similar verses
   - Return ranked results with citations

3. **Filtering Options**
   - Filter by book (e.g., only Book of Mormon)
   - Filter by language (EN/ES)
   - Filter by standard work

4. **Response Format**
   - Include book, chapter, verse, text
   - Include similarity score
   - Include context window

## Dependencies

- Phase 3 completed (embeddings generated)
- Azure Entra ID app registration
- AKS deployment configuration

## Success Criteria

- API accepts queries and returns relevant verses
- Authentication working with Azure Entra ID
- Response times under 500ms for typical queries

---

## Completion Notes

**Status**: COMPLETED
**Date**: 2026-01-12

### What Was Delivered

1. **FastAPI Project Structure** (`src/api/`)
   - `main.py` - App factory with CORS, router registration
   - `config.py` - Pydantic settings from environment
   - `dependencies.py` - DB session and embedding client injection

2. **Three Search Endpoints**
   - `POST /api/v1/scriptures/search` - Scripture semantic search
   - `POST /api/v1/cfm/search` - Come Follow Me lesson search
   - `POST /api/v1/conference/search` - Conference talk search

3. **Health Check Endpoints**
   - `GET /health` - Liveness probe
   - `GET /health/ready` - Readiness probe with DB check

4. **Filtering Support**
   - Scriptures: volume, book, language
   - CFM: year, testament, language
   - Conference: year, month, speaker (partial match)

5. **Integration Tests**
   - 66 passing tests covering all endpoints
   - Response time verification (<500ms)

### Deviations from Plan

- **Azure Entra ID deferred**: Authentication captured in `planning/backlog/azure-entra-id-authentication.md` for Azure deployment phase
- **Expanded scope**: Added CFM and Conference search (originally just scriptures)

### Performance Results

| Endpoint | Typical Response Time |
|----------|----------------------|
| Scripture search | ~300-400ms |
| CFM search | ~350-400ms |
| Conference search | ~350-450ms |

Note: ~200-300ms is embedding generation via Azure OpenAI; actual DB search is ~50-150ms.

### Commits

```
36c742d [PHASE] Add API integration tests
f2d8b39 [PHASE] Add conference talk search endpoint
9ab761d [PHASE] Add CFM lesson search endpoint
5e325ae [PHASE] Add scripture search endpoint
b075083 [PHASE] Add common schema definitions
906f3c5 [PHASE] Add dependencies and health check endpoints
f4faf18 [PHASE] Add FastAPI project setup
```

### How to Run

```bash
# Start the API
uvicorn src.api.main:app --reload --port 8000

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/scriptures/search \
  -H "Content-Type: application/json" \
  -d '{"query": "faith in Jesus Christ", "limit": 5}'

# Run tests
pytest tests/api/ -v

# OpenAPI docs
open http://localhost:8000/docs
```
