# Phase 7: Come Follow Me Integration

## Objective

Add Come Follow Me curriculum content as a separate searchable resource.

## High-Level Tasks

1. **Content Conversion**
   - Convert CFM PDFs to markdown (using Phase 1 process)
   - Parse lessons and study materials
   - Extract scripture references

2. **Schema Extension**
   - Create `come_follow_me` table
   - Store lesson content with year/week metadata
   - Link to referenced scriptures

3. **Yearly Refresh Process**
   - Document process for adding new year's curriculum
   - Handle curriculum versioning
   - Archive previous years

4. **Search Integration**
   - Include CFM content in search results
   - Filter by curriculum year
   - Show related lessons for scripture results

## Dependencies

- Phase 5 completed (RAG working)
- CFM PDFs converted to markdown

## Success Criteria

- CFM lessons searchable
- Scripture ↔ CFM lesson links working
- Process documented for yearly updates

## Content Files

Available PDFs (to be converted):
- 2023: New Testament
- 2024: Book of Mormon
- 2025: Doctrine & Covenants
- 2026: Old Testament
