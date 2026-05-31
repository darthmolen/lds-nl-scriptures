# ADR-001: Use HNSW Instead of IVFFlat for Vector Indexes

**Status**: Accepted
**Date**: 2026-01-13
**Supersedes**: None
**Decision Makers**: Development team

## Context

We are building a scripture search system using pgvector for semantic similarity search across ~42,000 verse embeddings. The initial implementation used IVFFlat indexes, which cluster vectors into lists and search a configurable number of lists (probes) at query time.

During precision evaluation, we discovered a critical problem: IVFFlat was missing highly relevant results. For example, when searching for "liahona compass", Alma 37:38 (the primary verse about the liahona, with similarity score 0.54) was not appearing in results, while less relevant verses like D&C 60:4 (similarity 0.36) appeared instead.

**Root cause**: The liahona verse was clustered into a different IVFFlat list than where the query vector landed. With the default probes setting, that list wasn't being searched.

**Workaround attempted**: Setting `ivfflat.probes = 100` (searching all 100 lists, essentially exact search) fixed the recall issue but defeated the purpose of approximate search.

**Forces at play**:
- Our dataset is static (~42K verses, rarely updated)
- Recall quality is critical for a scripture study tool
- Build time is not a concern (infrequent index rebuilds)
- Query latency matters but 42K vectors is small enough that both indexes are fast

## Decision

Switch from IVFFlat to HNSW (Hierarchical Navigable Small World) indexes for all vector similarity searches.

```sql
-- Before (IVFFlat)
CREATE INDEX idx_scriptures_embedding
ON scriptures
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- After (HNSW)
CREATE INDEX idx_scriptures_embedding
ON scriptures
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## Rationale

| Consideration | IVFFlat | HNSW (Chosen) |
|---------------|---------|---------------|
| Recall quality | Variable, depends on probes | Consistently high |
| Query speed | Fast with low probes | Fast |
| Build time | Fast | Slower (acceptable) |
| Memory usage | Lower | Higher (~2x, acceptable at our scale) |
| Tuning required | Yes (lists, probes) | Minimal (m, ef_construction, ef_search) |
| Best for | Frequently updated data | Static or rarely updated data |

### Why Not IVFFlat?

IVFFlat partitions vectors into Voronoi cells (lists). At query time, it only searches the nearest N lists (controlled by `probes`). This creates a fundamental tradeoff:

- **Low probes**: Fast but misses results in other cells
- **High probes**: Good recall but slow (approaches exact search)

For our use case with specific theological terms (liahona, Urim and Thummim), the clustering often separated semantically related verses. We had to set probes=100 to get acceptable recall, which meant we were doing nearly exact search anyway.

### Why HNSW?

HNSW builds a navigable graph where similar vectors are connected. Query traversal naturally follows high-similarity edges to find relevant results without needing to scan large portions of the index. This provides:

- Consistently high recall without parameter tuning
- Fast queries via graph traversal
- No "clustering miss" problem

## Consequences

### Positive

- Eliminated recall failures for specific term searches (liahona: 0% → 50%)
- Removed need for `SET ivfflat.probes = 100` workaround
- Simpler query code (no runtime parameter tuning)
- More predictable search quality across query types

### Negative

- Higher memory usage (~2x for the index structure)
- Slower index build time
- Cannot use WHERE filters as efficiently (HNSW doesn't support filtered search as well)

### Mitigations

- Memory: 42K vectors × 1536 dimensions is small; memory increase is negligible
- Build time: Indexes are rarely rebuilt; one-time cost is acceptable
- Filtering: For filtered queries (by volume/book), we search unfiltered then filter results

## Implementation Notes

Migration 005 handles the switch:
1. Drop existing IVFFlat indexes
2. Create HNSW indexes with m=16, ef_construction=64
3. Update search code to remove ivfflat.probes workaround

The HNSW parameters (m=16, ef_construction=64) are pgvector defaults and work well for our dataset size. If needed, we can increase ef_search at query time for higher recall.

## Files Changed

### Create

- `src/db/alembic/versions/005_switch_to_hnsw_indexes.py` - Migration to switch index types

### Modify

- `src/api/services/search.py` - Removed ivfflat.probes workaround
- `documentation/SEARCH-TUNING-VARIABLES.md` - Updated to document HNSW parameters

## References

- [pgvector HNSW documentation](https://github.com/pgvector/pgvector#hnsw)
- [HNSW paper: Efficient and robust approximate nearest neighbor search](https://arxiv.org/abs/1603.09320)
- [Understanding Vector Indexes](https://www.pinecone.io/learn/vector-database/)
