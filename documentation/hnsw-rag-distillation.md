# HNSW at Scale: RAG Retrieval Quality Reference

## The Core Problem

HNSW (Hierarchical Navigable Small World) powers most vector databases (Neo4j, Milvus, Weaviate, Qdrant, Pinecone, Azure AI Search). As your vector database grows, retrieval quality degrades silently—no errors, stable latency, but worse context fed to the LLM.

## HNSW Parameters

### Build-Time (Set Before Indexing)

| Parameter | Purpose | Typical Range | Trade-off |
|-----------|---------|---------------|-----------|
| **M** | Max connections per node per layer | 12–48 | Higher = better recall, more memory, slower indexing |
| **ef_construction** | Candidate set size during index build | 64–200 | Higher = better graph quality, slower build |

### Query-Time

| Parameter | Purpose | Trade-off |
|-----------|---------|-----------|
| **ef_search** | Candidates evaluated during search | Higher = better recall, higher latency |

## Key Findings from Experiments (50k–200k vectors)

1. **Flat search is the recall ceiling** — HNSW always underperforms flat search on recall
2. **HNSW degrades faster than flat search** as database grows (negative slope on overlap charts)
3. **ef_search=160** achieves >90% overlap with flat search but at 3x latency of ef_search=40
4. **Latency stays deceptively stable** while recall drops 10%+ from 50k to 200k vectors
5. **HNSW is O(log N)** vs flat search O(N) — orders of magnitude faster

### Latency Reference (ms, 200k vectors)

| Index Type | Search Time |
|------------|-------------|
| Flat | 18.4 |
| HNSW ef=40 | 0.15 |
| HNSW ef=160 | 0.41 |

## Recall@k Targets

| Metric | Acceptable Range |
|--------|------------------|
| Recall@5 | 70–90% |
| Recall@10 | 80–95% |

## Tuning Strategies

### 1. Monitor Retrieval Quality
- Maintain test set of known query → ground-truth chunk pairs
- Run recall evaluation at regular intervals
- Use LLM-as-judge: "Does retrieved context contain the answer?"

### 2. ef_search Tuning
- Start conservatively high, measure recall, reduce until latency acceptable
- Rebalance as database grows

### 3. Increase top_k Retrieval
- Retrieve top_k=15–20 instead of 3–10
- Let LLM filter relevant chunks during synthesis
- Higher recall with moderate ef_search

### 4. Hybrid Retrieval (Most Reliable at Scale)
- Apply metadata filters BEFORE vector search
- Options: SQL predicates, knowledge graphs, inverted indexes, category filters
- Narrows search space so vector similarity works on smaller candidate set

## Architecture Recommendation

```
User Query
    ↓
[Metadata Filter] ← SQL / Graph / Category lookup
    ↓
[Narrowed Vector Search] ← HNSW on filtered subset
    ↓
[Reranker] ← Optional cross-encoder
    ↓
[LLM Synthesis]
```

## Red Flags in Production

- Answer quality declining over time
- Users reporting "it used to find this"
- Growing corpus with unchanged HNSW settings
- No retrieval quality metrics in monitoring

## Implementation Checklist

- [ ] Document your M and ef_construction values
- [ ] Make ef_search configurable (not hardcoded)
- [ ] Create ground-truth test set for recall measurement
- [ ] Set up periodic recall evaluation
- [ ] Plan metadata filtering strategy for scale
- [ ] Monitor corpus growth rate

## For Scripture RAG Specifically

Consider metadata filters on:
- Book / Chapter / Verse references
- Testament (Old/New) or volume
- Topic tags or cross-references
- Speaker attribution
- Time period or dispensation

This reduces the vector search space significantly before HNSW runs.

---

*Source: "HNSW at Scale: Why Your RAG System Gets Worse as the Vector Database Grows" — Partha Sarkar, Towards Data Science, Jan 2026*
