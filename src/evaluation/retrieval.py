"""Retrieval precision measurement for Scripture Search using LLM-as-judge.

This module provides functionality to evaluate the retrieval quality
of the scripture vector search by measuring Precision@k metrics using
an LLM judge to assess verse relevance against a rubric.

Precision@k measures the proportion of retrieved documents that are
judged relevant by the LLM evaluator.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

from .config import get_settings
from .judge import JudgeLLM

logger = logging.getLogger(__name__)


# =============================================================================
# RETRIEVAL RELEVANCE RUBRIC PROMPT
# =============================================================================

RETRIEVAL_RELEVANCE_PROMPT = """You are evaluating whether a scripture verse is relevant to a search query.

## Task
Determine how relevant the retrieved verse is to the user's search query based on the relevance criteria.

## User Query
{query}

## Relevance Criteria
{relevance_rubric}

## Retrieved Verse
Reference: {reference}
Text: {text}

## Scoring
Rate the relevance on a scale of 1-3:
- Score 3 (Highly Relevant): Verse directly addresses the query topic or matches the relevance criteria strongly
- Score 2 (Partially Relevant): Verse is related to the topic but not a primary match, or partially meets the criteria
- Score 1 (Not Relevant): Verse is unrelated or only superficially connected to the query/criteria

## Response Format
Respond with EXACTLY this format (JSON):
{{"score": <1|2|3>, "reasoning": "<brief explanation>", "confidence": "<high|medium|low>"}}
"""


class SearchClient(Protocol):
    """Protocol for search client implementations.

    Any search client must implement a search method that accepts
    a query string and optional parameters, returning search results.
    """

    def search(
        self,
        query: str,
        limit: int = 10,
        lang: str = "en",
        **filters: Any,
    ) -> list[dict[str, Any]]:
        """Execute a search query.

        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            lang: Language code ('en' or 'es')
            **filters: Optional filters (volume, book, etc.)

        Returns:
            List of result dictionaries with 'reference' and 'text' keys
        """
        ...


@dataclass
class RetrievalTestCase:
    """A single retrieval test case from the ground truth set."""

    id: str
    query: str
    relevance_rubric: str
    top_k: int = 10
    description: str = ""
    category: str = "doctrinal_concept"
    lang: str = "en"
    filters: dict = field(default_factory=dict)


@dataclass
class JudgmentResult:
    """Result of judging a single verse's relevance."""

    reference: str
    text: str
    score: int  # 1-3
    reasoning: str
    confidence: str
    normalized_score: float  # 3->1.0, 2->0.5, 1->0.0


@dataclass
class PrecisionResult:
    """Result of evaluating precision for a single test case."""

    query: str
    relevance_rubric: str
    retrieved: list[dict]  # Full verse info
    judgments: list[JudgmentResult]
    precision_score: float  # sum of normalized scores / k
    k: int
    test_case_id: str = ""

    @property
    def highly_relevant_count(self) -> int:
        """Number of verses judged highly relevant (score 3)."""
        return sum(1 for j in self.judgments if j.score == 3)

    @property
    def partially_relevant_count(self) -> int:
        """Number of verses judged partially relevant (score 2)."""
        return sum(1 for j in self.judgments if j.score == 2)

    @property
    def not_relevant_count(self) -> int:
        """Number of verses judged not relevant (score 1)."""
        return sum(1 for j in self.judgments if j.score == 1)


@dataclass
class PrecisionReport:
    """Aggregated precision evaluation report."""

    total_cases: int
    precision_at_5: float
    precision_at_10: float
    precision_at_5_pass: bool
    precision_at_10_pass: bool
    by_category: dict[str, dict[str, Any]]
    results: list[PrecisionResult]
    timestamp: str = ""

    @property
    def overall_pass(self) -> bool:
        """Check if both precision thresholds are met."""
        return self.precision_at_5_pass and self.precision_at_10_pass


def normalize_score(score: int) -> float:
    """Normalize judgment score to 0-1 range.

    Args:
        score: Raw score (1, 2, or 3)

    Returns:
        Normalized score: 3->1.0, 2->0.5, 1->0.0
    """
    if score == 3:
        return 1.0
    elif score == 2:
        return 0.5
    else:
        return 0.0


def judge_verse_relevance(
    judge: JudgeLLM,
    query: str,
    relevance_rubric: str,
    reference: str,
    text: str,
) -> dict:
    """Judge the relevance of a single verse to a query.

    Args:
        judge: JudgeLLM instance
        query: The search query
        relevance_rubric: Criteria for relevance
        reference: Scripture reference (e.g., "1 Nephi 3:7")
        text: Full verse text

    Returns:
        Dict with score (1-3), reasoning, and confidence
    """
    prompt = RETRIEVAL_RELEVANCE_PROMPT.format(
        query=query,
        relevance_rubric=relevance_rubric,
        reference=reference,
        text=text,
    )

    try:
        response = judge.judge(prompt, max_tokens=200)

        # Parse JSON response
        # Handle potential markdown code blocks
        response_clean = response.strip()
        if response_clean.startswith("```"):
            lines = response_clean.split("\n")
            response_clean = "\n".join(lines[1:-1])

        result = json.loads(response_clean)

        # Validate score
        score = int(result.get("score", 1))
        if score not in [1, 2, 3]:
            score = 1

        return {
            "score": score,
            "reasoning": result.get("reasoning", "No reasoning provided"),
            "confidence": result.get("confidence", "medium"),
        }

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse judge response as JSON: {e}")
        logger.debug(f"Raw response: {response}")
        # Try to extract score from text
        if "score" in response.lower() and "3" in response:
            return {"score": 3, "reasoning": response, "confidence": "low"}
        elif "score" in response.lower() and "2" in response:
            return {"score": 2, "reasoning": response, "confidence": "low"}
        else:
            return {"score": 1, "reasoning": f"Parse error: {response}", "confidence": "low"}

    except Exception as e:
        logger.error(f"Judge error: {e}")
        return {"score": 1, "reasoning": f"Error: {str(e)}", "confidence": "low"}


def load_retrieval_ground_truth(path: Optional[str] = None) -> list[RetrievalTestCase]:
    """Load retrieval ground truth test cases from JSON file.

    Args:
        path: Path to ground truth file. Defaults to config setting.

    Returns:
        List of RetrievalTestCase objects
    """
    settings = get_settings()
    test_path = Path(path or settings.golden_test_path) / "retrieval_ground_truth.json"

    with open(test_path) as f:
        data = json.load(f)

    test_cases = []
    for tc in data.get("test_cases", []):
        test_cases.append(
            RetrievalTestCase(
                id=tc["id"],
                query=tc["query"],
                relevance_rubric=tc.get("relevance_rubric", ""),
                top_k=tc.get("top_k", 10),
                description=tc.get("description", ""),
                category=tc.get("category", "doctrinal_concept"),
                lang=tc.get("lang", "en"),
                filters=tc.get("filters", {}),
            )
        )

    logger.info(f"Loaded {len(test_cases)} retrieval test cases from {test_path}")
    return test_cases


def run_precision_evaluation(
    search_client: SearchClient,
    judge: Optional[JudgeLLM] = None,
    test_cases: Optional[list[RetrievalTestCase]] = None,
    k_values: tuple[int, int] = (5, 10),
) -> PrecisionReport:
    """Run retrieval precision evaluation using LLM-as-judge.

    Args:
        search_client: Search client implementing SearchClient protocol
        judge: JudgeLLM instance. If None, creates new instance.
        test_cases: Test cases to evaluate. If None, loads from ground truth file.
        k_values: Tuple of k values to evaluate (default: (5, 10))

    Returns:
        PrecisionReport with aggregated metrics and individual results
    """
    import time

    test_cases = test_cases or load_retrieval_ground_truth()
    settings = get_settings()

    # Initialize judge if not provided
    if judge is None:
        judge = JudgeLLM()

    results_at_5: list[PrecisionResult] = []
    results_at_10: list[PrecisionResult] = []

    # Track by category
    category_scores: dict[str, dict[str, list[float]]] = {}

    for tc in test_cases:
        logger.info(f"Evaluating: {tc.id} - {tc.query[:50]}...")

        try:
            # Execute search with max k
            max_k = max(k_values)
            search_results = search_client.search(
                query=tc.query,
                limit=max_k,
                lang=tc.lang,
                **tc.filters,
            )

            # Judge each result
            all_judgments: list[JudgmentResult] = []
            for result in search_results[:max_k]:
                reference = result.get("reference", "Unknown")
                text = result.get("text", "")

                judgment = judge_verse_relevance(
                    judge=judge,
                    query=tc.query,
                    relevance_rubric=tc.relevance_rubric,
                    reference=reference,
                    text=text,
                )

                all_judgments.append(
                    JudgmentResult(
                        reference=reference,
                        text=text,
                        score=judgment["score"],
                        reasoning=judgment["reasoning"],
                        confidence=judgment["confidence"],
                        normalized_score=normalize_score(judgment["score"]),
                    )
                )

            # Calculate precision at each k
            for k in k_values:
                judgments_at_k = all_judgments[:k]

                # Precision = sum of normalized scores / k
                if judgments_at_k:
                    precision = sum(j.normalized_score for j in judgments_at_k) / k
                else:
                    precision = 0.0

                result = PrecisionResult(
                    query=tc.query,
                    relevance_rubric=tc.relevance_rubric,
                    retrieved=search_results[:k],
                    judgments=judgments_at_k,
                    precision_score=precision,
                    k=k,
                    test_case_id=tc.id,
                )

                if k == 5:
                    results_at_5.append(result)
                elif k == 10:
                    results_at_10.append(result)

                # Track by category
                if tc.category not in category_scores:
                    category_scores[tc.category] = {"at_5": [], "at_10": []}

                if k == 5:
                    category_scores[tc.category]["at_5"].append(precision)
                elif k == 10:
                    category_scores[tc.category]["at_10"].append(precision)

                logger.debug(f"  Precision@{k}: {precision:.2%}")

        except Exception as e:
            logger.error(f"Error evaluating {tc.id}: {e}")
            # Add zero-score results for failed cases
            for k in k_values:
                result = PrecisionResult(
                    query=tc.query,
                    relevance_rubric=tc.relevance_rubric,
                    retrieved=[],
                    judgments=[],
                    precision_score=0.0,
                    k=k,
                    test_case_id=tc.id,
                )
                if k == 5:
                    results_at_5.append(result)
                elif k == 10:
                    results_at_10.append(result)

    # Calculate aggregate metrics
    avg_precision_at_5 = (
        sum(r.precision_score for r in results_at_5) / len(results_at_5)
        if results_at_5
        else 0.0
    )
    avg_precision_at_10 = (
        sum(r.precision_score for r in results_at_10) / len(results_at_10)
        if results_at_10
        else 0.0
    )

    # Calculate by-category averages
    by_category = {}
    for category, scores in category_scores.items():
        by_category[category] = {
            "precision_at_5": sum(scores["at_5"]) / len(scores["at_5"]) if scores["at_5"] else 0.0,
            "precision_at_10": sum(scores["at_10"]) / len(scores["at_10"]) if scores["at_10"] else 0.0,
            "count": len(scores["at_5"]),
        }

    # Combine results (use precision@10 results as primary)
    all_results = results_at_10

    # Get thresholds from settings, default to 0.75 and 0.70
    precision_at_5_threshold = getattr(settings, "precision_at_5_threshold", 0.75)
    precision_at_10_threshold = getattr(settings, "precision_at_10_threshold", 0.70)

    return PrecisionReport(
        total_cases=len(test_cases),
        precision_at_5=avg_precision_at_5,
        precision_at_10=avg_precision_at_10,
        precision_at_5_pass=avg_precision_at_5 >= precision_at_5_threshold,
        precision_at_10_pass=avg_precision_at_10 >= precision_at_10_threshold,
        by_category=by_category,
        results=all_results,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def print_precision_report(report: PrecisionReport, verbose: bool = False) -> None:
    """Print a formatted precision evaluation report to console.

    Args:
        report: PrecisionReport to display
        verbose: If True, show detailed judgments for each test case
    """
    settings = get_settings()

    # Get thresholds
    p5_threshold = getattr(settings, "precision_at_5_threshold", 0.75)
    p10_threshold = getattr(settings, "precision_at_10_threshold", 0.70)

    print("\n" + "=" * 70)
    print("RETRIEVAL PRECISION EVALUATION REPORT (LLM-as-Judge)")
    print("=" * 70)
    print(f"Timestamp: {report.timestamp}")
    print(f"Total test cases: {report.total_cases}")

    # Overall metrics
    print("\n--- Overall Metrics ---")
    p5_status = "PASS" if report.precision_at_5_pass else "FAIL"
    p10_status = "PASS" if report.precision_at_10_pass else "FAIL"

    print(f"  Precision@5:  {report.precision_at_5:.1%} (threshold: {p5_threshold:.0%}) [{p5_status}]")
    print(f"  Precision@10: {report.precision_at_10:.1%} (threshold: {p10_threshold:.0%}) [{p10_status}]")

    # By category
    print("\n--- By Category ---")
    for category, metrics in sorted(report.by_category.items()):
        print(f"  {category} (n={metrics['count']}):")
        print(f"    Precision@5:  {metrics['precision_at_5']:.1%}")
        print(f"    Precision@10: {metrics['precision_at_10']:.1%}")

    # Individual results
    print("\n--- Test Case Results ---")
    for result in sorted(report.results, key=lambda x: x.precision_score):
        highly_rel = result.highly_relevant_count
        partial_rel = result.partially_relevant_count
        not_rel = result.not_relevant_count

        print(f"\n  [{result.test_case_id}] {result.query[:50]}...")
        print(f"    Precision@{result.k}: {result.precision_score:.1%}")
        print(f"    Relevance: {highly_rel} high, {partial_rel} partial, {not_rel} not relevant")

        if verbose:
            print(f"    Rubric: {result.relevance_rubric[:80]}...")
            print("    Judgments:")
            for j in result.judgments:
                score_label = {3: "HIGH", 2: "PARTIAL", 1: "NOT REL"}[j.score]
                print(f"      - [{score_label}] {j.reference}: {j.reasoning[:60]}...")

    # Summary
    print("\n" + "-" * 70)
    overall = "PASS" if report.overall_pass else "FAIL"
    print(f"Overall Status: [{overall}]")
    print("=" * 70)


def create_api_search_client(
    base_url: str = "http://localhost:8000",
) -> SearchClient:
    """Create a search client that calls the Scripture Search API.

    Args:
        base_url: Base URL of the API server

    Returns:
        SearchClient implementation using HTTP requests
    """
    import httpx

    class APISearchClient:
        """Search client that calls the Scripture Search REST API."""

        def __init__(self, base_url: str):
            self.base_url = base_url.rstrip("/")
            self.client = httpx.Client(timeout=30.0)

        def search(
            self,
            query: str,
            limit: int = 10,
            lang: str = "en",
            **filters: Any,
        ) -> list[dict[str, Any]]:
            """Execute search via API."""
            payload = {
                "query": query,
                "limit": limit,
                "lang": lang,
            }

            # Add optional filters
            if "volume" in filters:
                payload["volume"] = filters["volume"]
            if "book" in filters:
                payload["book"] = filters["book"]

            response = self.client.post(
                f"{self.base_url}/api/v1/scriptures/search",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            return data.get("results", [])

    return APISearchClient(base_url)


def create_direct_search_client(session_factory: Callable) -> SearchClient:
    """Create a search client that calls the search service directly.

    Args:
        session_factory: Callable that returns a database session

    Returns:
        SearchClient implementation using direct service calls
    """
    from src.api.services.scriptures import search_scriptures
    from src.embeddings.client import get_single_embedding

    class DirectSearchClient:
        """Search client that calls the search service directly."""

        def __init__(self, session_factory: Callable):
            self.session_factory = session_factory

        def search(
            self,
            query: str,
            limit: int = 10,
            lang: str = "en",
            **filters: Any,
        ) -> list[dict[str, Any]]:
            """Execute search directly via service."""
            # Get embedding
            query_embedding = get_single_embedding(query)

            # Execute hybrid search (vector + full-text)
            with self.session_factory() as session:
                results = search_scriptures(
                    session=session,
                    query_embedding=query_embedding,
                    lang=lang,
                    limit=limit,
                    volume=filters.get("volume"),
                    book=filters.get("book"),
                    query_text=query,  # Pass original query for hybrid search
                    use_hybrid=True,
                )

            return results

    return DirectSearchClient(session_factory)
