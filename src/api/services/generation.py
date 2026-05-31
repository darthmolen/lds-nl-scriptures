"""RAG generation service.

This module provides the GenerationService for RAG-based question answering
using scripture search results as context for LLM generation.
"""

import os
import re
import time
from typing import Optional

from openai import AzureOpenAI
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from src.api.services.scriptures import search_scriptures
from src.embeddings.client import get_single_embedding


# System prompt for scripture-based question answering
SYSTEM_PROMPT = """You are a helpful assistant that answers questions about scripture using provided context.

Instructions:
1. Answer the question based ONLY on the provided scripture verses.
2. If the scriptures don't contain relevant information, say so honestly.
3. When citing scriptures, use the exact reference format provided (e.g., "Alma 32:21").
4. Include scripture references inline in your answer using brackets, like [Alma 32:21].
5. Be reverent and respectful when discussing sacred texts.
6. Provide clear, helpful answers that are grounded in the scripture context.
7. If asked in Spanish, respond in Spanish.

Do not invent or fabricate scripture references. Only cite verses from the provided context."""


def _get_generation_client() -> AzureOpenAI:
    """Create Azure OpenAI client for generation.

    Returns:
        AzureOpenAI client configured for chat completions.
    """
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )


def _format_context(results: list[dict]) -> str:
    """Format search results into context for the LLM.

    Args:
        results: List of scripture search result dictionaries.

    Returns:
        Formatted string of scripture verses for context.
    """
    if not results:
        return "No relevant scriptures found."

    context_parts = []
    for i, result in enumerate(results, 1):
        reference = result["reference"]
        text = result["text"]
        context_parts.append(f"{i}. [{reference}]\n{text}")

    return "\n\n".join(context_parts)


def _extract_citations(answer: str, results: list[dict]) -> list[dict]:
    """Extract citations from the generated answer.

    Finds scripture references mentioned in the answer and matches them
    to the provided search results.

    Args:
        answer: The generated answer text.
        results: List of scripture search result dictionaries.

    Returns:
        List of citation dictionaries with reference and text.
    """
    # Build a lookup of references to results
    ref_lookup = {r["reference"].lower(): r for r in results}

    # Find all bracketed references in the answer
    # Matches patterns like [Alma 32:21], [1 Nephi 3:7], [D&C 121:7-8]
    pattern = r"\[([^\]]+)\]"
    matches = re.findall(pattern, answer)

    citations = []
    seen_refs = set()

    for match in matches:
        ref_lower = match.lower()
        # Try exact match first
        if ref_lower in ref_lookup and ref_lower not in seen_refs:
            result = ref_lookup[ref_lower]
            citations.append({
                "reference": result["reference"],
                "text": result["text"],
            })
            seen_refs.add(ref_lower)
        else:
            # Try partial matching for verse ranges or variations
            for ref_key, result in ref_lookup.items():
                if ref_key not in seen_refs:
                    # Check if the match starts with the reference
                    if ref_lower.startswith(ref_key) or ref_key.startswith(ref_lower.split("-")[0]):
                        citations.append({
                            "reference": result["reference"],
                            "text": result["text"],
                        })
                        seen_refs.add(ref_key)
                        break

    return citations


class GenerationService:
    """Service for RAG-based question answering.

    Combines scripture semantic search with LLM generation to answer
    questions about scripture with citations.

    Attributes:
        model: Azure OpenAI model deployment name for generation.
        max_tokens: Maximum tokens for generated response.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ):
        """Initialize the generation service.

        Args:
            model: Azure OpenAI model deployment name. Defaults to
                AZURE_OPENAI_GENERATION_DEPLOYMENT env var or 'gpt-4o-mini'.
            max_tokens: Maximum tokens for response. Defaults to
                AZURE_OPENAI_MAX_TOKENS env var or 1024.
        """
        self.model = model or os.getenv(
            "AZURE_OPENAI_GENERATION_DEPLOYMENT", "gpt-4o-mini"
        )
        self.max_tokens = max_tokens or int(
            os.getenv("AZURE_OPENAI_MAX_TOKENS", "1024")
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _generate_completion(
        self,
        question: str,
        context: str,
    ) -> str:
        """Generate a completion using Azure OpenAI.

        Args:
            question: The user's question.
            context: Formatted scripture context.

        Returns:
            Generated answer text.

        Raises:
            Exception: If generation fails after retries.
        """
        client = _get_generation_client()

        user_message = f"""Context (scripture verses):
{context}

Question: {question}

Please answer the question based on the provided scripture verses. Include scripture references in brackets."""

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=self.max_tokens,
            temperature=0.7,
        )

        return response.choices[0].message.content

    def ask(
        self,
        session: Session,
        question: str,
        lang: str = "en",
        top_k: int = 10,
        filters: Optional[dict] = None,
    ) -> dict:
        """Answer a question using RAG with scripture context.

        Performs semantic search for relevant scriptures, then generates
        an answer using the LLM with the scriptures as context.

        Args:
            session: SQLAlchemy database session.
            question: The question to answer.
            lang: Language code ('en' or 'es').
            top_k: Number of scripture results to use as context.
            filters: Optional filters for scripture search (volume, book).

        Returns:
            Dictionary with answer, citations, and metadata.

        Raises:
            Exception: If embedding or generation fails.
        """
        filters = filters or {}

        # Phase 1: Search for relevant scriptures
        search_start = time.perf_counter()

        query_embedding = get_single_embedding(question)
        results = search_scriptures(
            session=session,
            query_embedding=query_embedding,
            lang=lang,
            limit=top_k,
            volume=filters.get("volume"),
            book=filters.get("book"),
        )

        search_time_ms = (time.perf_counter() - search_start) * 1000

        # Phase 2: Format context and generate answer
        gen_start = time.perf_counter()

        context = _format_context(results)
        answer = self._generate_completion(question, context)

        generation_time_ms = (time.perf_counter() - gen_start) * 1000

        # Phase 3: Extract citations
        citations = _extract_citations(answer, results)

        return {
            "answer": answer,
            "citations": citations,
            "meta": {
                "model": self.model,
                "search_time_ms": round(search_time_ms, 2),
                "generation_time_ms": round(generation_time_ms, 2),
                "context_verses": len(results),
            },
        }


# Module-level service instance for convenience
_default_service: Optional[GenerationService] = None


def get_generation_service() -> GenerationService:
    """Get the default generation service instance.

    Returns:
        GenerationService: Cached service instance.
    """
    global _default_service
    if _default_service is None:
        _default_service = GenerationService()
    return _default_service
