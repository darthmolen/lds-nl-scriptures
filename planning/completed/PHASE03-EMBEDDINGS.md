# Phase 3: Embedding Generation

## Objective

Generate vector embeddings for all scripture verses using OpenAI's text-embedding-3-small.

## High-Level Tasks

1. **Embedding Service**
   - Create service to call OpenAI embeddings API
   - Handle rate limiting and batching
   - Implement retry logic for API failures

2. **Embedding Text Construction**
   - Use chunking strategy from CLAUDE.md
   - Include book, chapter, verse, context in embedding text
   - Optimize for semantic search quality

3. **Batch Processing**
   - Process verses in batches (avoid API limits)
   - Store embeddings in pgvector column
   - Track progress for resumability

4. **Index Creation**
   - Create IVFFlat index for cosine similarity
   - Tune index parameters for performance

## Dependencies

- Phase 2 completed (verses in database)
- OpenAI API key with embeddings access
- Sufficient API budget for ~40k+ verses

## Success Criteria

- All verses have 1536-dimension embeddings
- Index created and queryable
- Sample semantic searches return relevant results
