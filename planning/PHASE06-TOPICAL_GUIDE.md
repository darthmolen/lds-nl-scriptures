# Phase 6: Topical Guide Integration

## Objective

Add relational Topical Guide data to enhance search with topic-based lookups.

## High-Level Tasks

1. **Data Source**
   - Identify Topical Guide data source
   - Parse topic → scripture mappings
   - Handle subtopics and cross-references

2. **Schema Extension**
   - Create `topical_guide` table
   - Link topics to scripture IDs
   - Support topic hierarchy

3. **Enhanced Search**
   - After vector search, lookup related topics
   - Pull additional verses from matched topics
   - Merge and deduplicate results

4. **Topic Browsing**
   - Endpoint to list all topics
   - Endpoint to get verses by topic
   - Support topic search

## Dependencies

- Phase 4 completed (search API working)
- Topical Guide data source identified

## Success Criteria

- Topics linked to scripture verses
- Search augmented with topical results
- Topic browsing functional
