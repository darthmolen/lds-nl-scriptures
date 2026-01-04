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
