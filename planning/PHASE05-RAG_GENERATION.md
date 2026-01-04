# Phase 5: RAG Generation

## Objective

Add response generation using gpt-4o-mini to synthesize answers with scripture citations.

## High-Level Tasks

1. **Generation Endpoint**
   - Accept user question
   - Retrieve relevant verses via search
   - Generate response with citations

2. **Prompt Engineering**
   - Design system prompt for scripture assistant
   - Include retrieved verses as context
   - Enforce citation format

3. **Response Format**
   - Natural language answer
   - Inline scripture citations
   - List of referenced verses

4. **Guardrails**
   - Limit to scripture-based responses
   - Handle off-topic queries gracefully
   - Token/cost management

## Dependencies

- Phase 4 completed (search API working)
- OpenAI API key with GPT-4o-mini access

## Success Criteria

- Questions answered with relevant scripture context
- All claims properly cited
- Responses theologically appropriate
