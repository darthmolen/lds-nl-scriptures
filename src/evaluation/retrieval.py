"""Retrieval recall measurement for Scripture Search.

This module provides functionality to evaluate the retrieval quality
of the scripture vector search by measuring Recall@k metrics against
a ground truth test set.

Recall@k measures the proportion of expected relevant documents
that appear within the top-k search results.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

from .config import get_settings

logger = logging.getLogger(__name__)


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
            List of result dictionaries with 'reference' key
        """
        ...


@dataclass
class RetrievalTestCase:
    """A single retrieval test case from the ground truth set."""

    id: str
    query: str
    expected_verses: list[str]
    top_k: int = 10
    description: str = ""
    category: str = "simple"
    lang: str = "en"
    filters: dict = field(default_factory=dict)


@dataclass
class RecallResult:
    """Result of evaluating recall for a single test case."""

    query: str
    expected: list[str]
    retrieved: list[str]
    recall_score: float
    k: int
    test_case_id: str = ""
    hits: list[str] = field(default_factory=list)
    misses: list[str] = field(default_factory=list)

    @property
    def hit_count(self) -> int:
        """Number of expected verses found in retrieved results."""
        return len(self.hits)

    @property
    def expected_count(self) -> int:
        """Total number of expected verses."""
        return len(self.expected)


@dataclass
class RecallReport:
    """Aggregated recall evaluation report."""

    total_cases: int
    recall_at_5: float
    recall_at_10: float
    recall_at_5_pass: bool
    recall_at_10_pass: bool
    by_category: dict[str, dict[str, float]]
    results: list[RecallResult]
    timestamp: str = ""

    @property
    def overall_pass(self) -> bool:
        """Check if both recall thresholds are met."""
        return self.recall_at_5_pass and self.recall_at_10_pass


def normalize_reference(reference: str) -> str:
    """Normalize a scripture reference for comparison.

    Handles variations in formatting:
    - Removes extra whitespace
    - Standardizes book names (e.g., '1 Nephi' vs '1Nephi')
    - Handles chapter:verse vs chapter.verse

    Args:
        reference: Raw scripture reference string

    Returns:
        Normalized reference for comparison
    """
    # Remove extra whitespace and lowercase
    ref = " ".join(reference.strip().split()).lower()

    # Replace common variations
    ref = ref.replace(".", ":")
    ref = ref.replace("  ", " ")

    # Standardize book abbreviations
    replacements = {
        "1ne": "1 nephi",
        "2ne": "2 nephi",
        "1 ne": "1 nephi",
        "2 ne": "2 nephi",
        "d&c": "doctrine and covenants",
        "dc": "doctrine and covenants",
        "js-h": "joseph smith-history",
        "js-m": "joseph smith-matthew",
        "a of f": "articles of faith",
    }

    for abbrev, full in replacements.items():
        if ref.startswith(abbrev + " "):
            ref = full + ref[len(abbrev):]

    return ref


def calculate_recall(
    expected: list[str],
    retrieved: list[str],
    k: int,
) -> tuple[float, list[str], list[str]]:
    """Calculate Recall@k for a single query.

    Recall@k = |relevant retrieved| / |total relevant|

    Args:
        expected: List of expected/relevant scripture references
        retrieved: List of retrieved scripture references (in rank order)
        k: Number of top results to consider

    Returns:
        Tuple of (recall_score, hits, misses) where:
        - recall_score: Proportion of expected items found in top-k
        - hits: Expected items that were found
        - misses: Expected items that were not found
    """
    if not expected:
        return 1.0, [], []

    # Normalize all references for comparison
    expected_normalized = {normalize_reference(ref) for ref in expected}
    retrieved_normalized = [normalize_reference(ref) for ref in retrieved[:k]]

    # Find hits and misses
    hits = []
    misses = []

    for exp_ref, exp_norm in zip(expected, expected_normalized):
        # Check if any retrieved reference matches (partial matching for verses)
        found = False
        for ret_norm in retrieved_normalized:
            # Allow partial match for verse ranges
            if exp_norm in ret_norm or ret_norm in exp_norm:
                found = True
                break
            # Also check if chapter:verse matches (ignoring book variations)
            exp_parts = exp_norm.split()
            ret_parts = ret_norm.split()
            if len(exp_parts) >= 2 and len(ret_parts) >= 2:
                if exp_parts[-1] == ret_parts[-1]:  # Same chapter:verse
                    # Check if book names are similar enough
                    exp_book = " ".join(exp_parts[:-1])
                    ret_book = " ".join(ret_parts[:-1])
                    if exp_book in ret_book or ret_book in exp_book:
                        found = True
                        break

        if found:
            hits.append(exp_ref)
        else:
            misses.append(exp_ref)

    recall = len(hits) / len(expected)
    return recall, hits, misses


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
                expected_verses=tc.get("expected_verses", []),
                top_k=tc.get("top_k", 10),
                description=tc.get("description", ""),
                category=tc.get("category", "simple"),
                lang=tc.get("lang", "en"),
                filters=tc.get("filters", {}),
            )
        )

    logger.info(f"Loaded {len(test_cases)} retrieval test cases from {test_path}")
    return test_cases


def run_recall_evaluation(
    search_client: SearchClient,
    test_cases: Optional[list[RetrievalTestCase]] = None,
    k_values: tuple[int, int] = (5, 10),
) -> RecallReport:
    """Run retrieval recall evaluation against ground truth.

    Args:
        search_client: Search client implementing SearchClient protocol
        test_cases: Test cases to evaluate. If None, loads from ground truth file.
        k_values: Tuple of k values to evaluate (default: (5, 10))

    Returns:
        RecallReport with aggregated metrics and individual results
    """
    import time

    test_cases = test_cases or load_retrieval_ground_truth()
    settings = get_settings()

    results_at_5: list[RecallResult] = []
    results_at_10: list[RecallResult] = []

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

            # Extract references from results
            retrieved_refs = [
                r.get("reference", "") for r in search_results if r.get("reference")
            ]

            # Calculate recall at each k
            for k in k_values:
                recall, hits, misses = calculate_recall(
                    expected=tc.expected_verses,
                    retrieved=retrieved_refs,
                    k=k,
                )

                result = RecallResult(
                    query=tc.query,
                    expected=tc.expected_verses,
                    retrieved=retrieved_refs[:k],
                    recall_score=recall,
                    k=k,
                    test_case_id=tc.id,
                    hits=hits,
                    misses=misses,
                )

                if k == 5:
                    results_at_5.append(result)
                elif k == 10:
                    results_at_10.append(result)

                # Track by category
                if tc.category not in category_scores:
                    category_scores[tc.category] = {"at_5": [], "at_10": []}

                if k == 5:
                    category_scores[tc.category]["at_5"].append(recall)
                elif k == 10:
                    category_scores[tc.category]["at_10"].append(recall)

                logger.debug(f"  Recall@{k}: {recall:.2%} ({len(hits)}/{len(tc.expected_verses)} hits)")

        except Exception as e:
            logger.error(f"Error evaluating {tc.id}: {e}")
            # Add zero-score results for failed cases
            for k in k_values:
                result = RecallResult(
                    query=tc.query,
                    expected=tc.expected_verses,
                    retrieved=[],
                    recall_score=0.0,
                    k=k,
                    test_case_id=tc.id,
                    hits=[],
                    misses=tc.expected_verses,
                )
                if k == 5:
                    results_at_5.append(result)
                elif k == 10:
                    results_at_10.append(result)

    # Calculate aggregate metrics
    avg_recall_at_5 = (
        sum(r.recall_score for r in results_at_5) / len(results_at_5)
        if results_at_5
        else 0.0
    )
    avg_recall_at_10 = (
        sum(r.recall_score for r in results_at_10) / len(results_at_10)
        if results_at_10
        else 0.0
    )

    # Calculate by-category averages
    by_category = {}
    for category, scores in category_scores.items():
        by_category[category] = {
            "recall_at_5": sum(scores["at_5"]) / len(scores["at_5"]) if scores["at_5"] else 0.0,
            "recall_at_10": sum(scores["at_10"]) / len(scores["at_10"]) if scores["at_10"] else 0.0,
            "count": len(scores["at_5"]),
        }

    # Combine results (use recall@10 results as primary)
    all_results = results_at_10

    return RecallReport(
        total_cases=len(test_cases),
        recall_at_5=avg_recall_at_5,
        recall_at_10=avg_recall_at_10,
        recall_at_5_pass=avg_recall_at_5 >= settings.recall_at_5_threshold,
        recall_at_10_pass=avg_recall_at_10 >= settings.recall_at_10_threshold,
        by_category=by_category,
        results=all_results,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def print_recall_report(report: RecallReport) -> None:
    """Print a formatted recall evaluation report to console.

    Args:
        report: RecallReport to display
    """
    settings = get_settings()

    print("\n" + "=" * 60)
    print("RETRIEVAL RECALL EVALUATION REPORT")
    print("=" * 60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Total test cases: {report.total_cases}")

    # Overall metrics
    print("\n--- Overall Metrics ---")
    r5_status = "PASS" if report.recall_at_5_pass else "FAIL"
    r10_status = "PASS" if report.recall_at_10_pass else "FAIL"
    r5_threshold = settings.recall_at_5_threshold
    r10_threshold = settings.recall_at_10_threshold

    print(f"  Recall@5:  {report.recall_at_5:.1%} (threshold: {r5_threshold:.0%}) [{r5_status}]")
    print(f"  Recall@10: {report.recall_at_10:.1%} (threshold: {r10_threshold:.0%}) [{r10_status}]")

    # By category
    print("\n--- By Category ---")
    for category, metrics in sorted(report.by_category.items()):
        print(f"  {category} (n={metrics['count']}):")
        print(f"    Recall@5:  {metrics['recall_at_5']:.1%}")
        print(f"    Recall@10: {metrics['recall_at_10']:.1%}")

    # Failed cases (recall < 1.0)
    failed_cases = [r for r in report.results if r.recall_score < 1.0]
    if failed_cases:
        print(f"\n--- Cases with Missing Results ({len(failed_cases)}) ---")
        for result in sorted(failed_cases, key=lambda x: x.recall_score):
            print(f"\n  [{result.test_case_id}] {result.query[:50]}...")
            print(f"    Recall@{result.k}: {result.recall_score:.1%}")
            print(f"    Hits ({len(result.hits)}): {', '.join(result.hits[:5])}")
            if result.misses:
                print(f"    Misses ({len(result.misses)}): {', '.join(result.misses[:5])}")

    # Summary
    print("\n" + "-" * 60)
    overall = "PASS" if report.overall_pass else "FAIL"
    print(f"Overall Status: [{overall}]")
    print("=" * 60)


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

            # Execute search
            with self.session_factory() as session:
                results = search_scriptures(
                    session=session,
                    query_embedding=query_embedding,
                    lang=lang,
                    limit=limit,
                    volume=filters.get("volume"),
                    book=filters.get("book"),
                )

            return results

    return DirectSearchClient(session_factory)
