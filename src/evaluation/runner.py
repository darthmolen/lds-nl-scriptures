"""Evaluation runner for Scripture RAG system.

Runs golden test cases through the RAG system and evaluates with LLM-as-judge.
"""

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import get_settings
from .judge import JudgeLLM, get_judge
from .rubrics import Dimension, calculate_weighted_score, get_all_rubrics, get_rubric

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """A single test case from the golden set."""

    id: str
    question: str
    complexity: str
    expected_citations: list[str]
    expected_themes: list[str] = field(default_factory=list)
    filters: dict = field(default_factory=dict)
    description: str = ""
    notes: str = ""


@dataclass
class EvaluationResult:
    """Result of evaluating a single test case."""

    test_case_id: str
    question: str
    answer: str
    citations: list[dict]
    dimension_results: dict[Dimension, bool]
    dimension_verdicts: dict[Dimension, str]
    weighted_score: float
    passed: bool
    search_time_ms: float = 0.0
    generation_time_ms: float = 0.0


@dataclass
class EvaluationReport:
    """Overall evaluation report for a test run."""

    total_cases: int
    passed_cases: int
    pass_rate: float
    dimension_pass_rates: dict[str, float]
    by_complexity: dict[str, dict]
    results: list[EvaluationResult]
    timestamp: str = ""


def load_golden_test_set(path: Optional[str] = None) -> list[TestCase]:
    """Load golden test cases from JSON file.

    Args:
        path: Path to golden test file. Defaults to config setting.

    Returns:
        List of TestCase objects
    """
    settings = get_settings()
    test_path = Path(path or settings.golden_test_path) / "scripture_qa.json"

    with open(test_path) as f:
        data = json.load(f)

    test_cases = []
    for tc in data.get("test_cases", []):
        test_cases.append(
            TestCase(
                id=tc["id"],
                question=tc["question"],
                complexity=tc["complexity"],
                expected_citations=tc.get("expected_citations", []),
                expected_themes=tc.get("expected_themes", []),
                filters=tc.get("filters", {}),
                description=tc.get("description", ""),
                notes=tc.get("notes", ""),
            )
        )

    logger.info(f"Loaded {len(test_cases)} test cases from {test_path}")
    return test_cases


def parse_verdict(verdict: str) -> tuple[bool, str]:
    """Parse a judge verdict into pass/fail and reason.

    Args:
        verdict: Raw verdict string from judge

    Returns:
        Tuple of (passed: bool, reason: str)
    """
    verdict = verdict.strip()

    if verdict.upper().startswith("PASS"):
        # Extract reason after PASS:
        match = re.match(r"PASS[:\s]*(.+)", verdict, re.IGNORECASE | re.DOTALL)
        reason = match.group(1).strip() if match else "Passed"
        return True, reason
    elif verdict.upper().startswith("FAIL"):
        match = re.match(r"FAIL[:\s]*(.+)", verdict, re.IGNORECASE | re.DOTALL)
        reason = match.group(1).strip() if match else "Failed"
        return False, reason
    elif verdict.upper().startswith("N/A"):
        # N/A counts as pass (not applicable to this case)
        return True, "Not applicable"
    else:
        # Ambiguous - log and treat as fail
        logger.warning(f"Ambiguous verdict: {verdict[:100]}")
        return False, f"Ambiguous verdict: {verdict[:100]}"


def evaluate_response(
    judge: JudgeLLM,
    question: str,
    answer: str,
    citations: list[dict],
    retrieved_context: str = "",
) -> tuple[dict[Dimension, bool], dict[Dimension, str]]:
    """Evaluate a RAG response using all rubrics.

    Args:
        judge: JudgeLLM instance
        question: Original user question
        answer: Generated answer
        citations: List of citation dicts with 'reference' and 'text'
        retrieved_context: Full retrieved context

    Returns:
        Tuple of (dimension_results, dimension_verdicts)
    """
    results = {}
    verdicts = {}

    for rubric in get_all_rubrics():
        prompt = rubric.build_prompt(
            question=question,
            answer=answer,
            citations=citations,
            retrieved_context=retrieved_context,
        )

        try:
            verdict = judge.judge(prompt)
            passed, reason = parse_verdict(verdict)
            results[rubric.dimension] = passed
            verdicts[rubric.dimension] = reason

            logger.debug(
                f"  {rubric.dimension.value}: {'PASS' if passed else 'FAIL'} - {reason[:50]}"
            )
        except Exception as e:
            logger.error(f"Error evaluating {rubric.dimension.value}: {e}")
            results[rubric.dimension] = False
            verdicts[rubric.dimension] = f"Error: {str(e)}"

    return results, verdicts


def run_evaluation(
    rag_client,
    judge: Optional[JudgeLLM] = None,
    test_cases: Optional[list[TestCase]] = None,
) -> EvaluationReport:
    """Run full evaluation on golden test set.

    Args:
        rag_client: Client with ask(question, filters) method
        judge: JudgeLLM instance. If None, creates new one.
        test_cases: Test cases to run. If None, loads from golden set.

    Returns:
        EvaluationReport with all results
    """
    judge = judge or get_judge()
    test_cases = test_cases or load_golden_test_set()

    settings = get_settings()
    results = []

    # Track by dimension
    dimension_passes = {d: 0 for d in Dimension}
    dimension_totals = {d: 0 for d in Dimension}

    # Track by complexity
    complexity_results = {
        "simple": {"passed": 0, "total": 0},
        "medium": {"passed": 0, "total": 0},
        "complex": {"passed": 0, "total": 0},
    }

    for tc in test_cases:
        logger.info(f"Evaluating: {tc.id} - {tc.question[:50]}...")

        try:
            # Call RAG system
            start_time = time.time()
            response = rag_client.ask(tc.question, filters=tc.filters)
            total_time = (time.time() - start_time) * 1000

            answer = response.get("answer", "")
            citations = response.get("citations", [])
            search_time = response.get("meta", {}).get("search_time_ms", 0)
            gen_time = response.get("meta", {}).get("generation_time_ms", total_time)

            # Build retrieved context for source_relevance rubric
            retrieved_context = "\n".join(
                f"- {c.get('reference', '')}: {c.get('text', '')}" for c in citations
            )

            # Evaluate with judge
            dim_results, dim_verdicts = evaluate_response(
                judge=judge,
                question=tc.question,
                answer=answer,
                citations=citations,
                retrieved_context=retrieved_context,
            )

            # Calculate scores
            weighted_score = calculate_weighted_score(dim_results)
            passed = weighted_score >= settings.pass_threshold

            result = EvaluationResult(
                test_case_id=tc.id,
                question=tc.question,
                answer=answer,
                citations=citations,
                dimension_results=dim_results,
                dimension_verdicts=dim_verdicts,
                weighted_score=weighted_score,
                passed=passed,
                search_time_ms=search_time,
                generation_time_ms=gen_time,
            )
            results.append(result)

            # Update tracking
            for dim, passed_dim in dim_results.items():
                dimension_totals[dim] += 1
                if passed_dim:
                    dimension_passes[dim] += 1

            complexity_results[tc.complexity]["total"] += 1
            if passed:
                complexity_results[tc.complexity]["passed"] += 1

            logger.info(f"  Score: {weighted_score:.2f} - {'PASS' if passed else 'FAIL'}")

        except Exception as e:
            logger.error(f"Error running test case {tc.id}: {e}")
            # Create failed result
            results.append(
                EvaluationResult(
                    test_case_id=tc.id,
                    question=tc.question,
                    answer="",
                    citations=[],
                    dimension_results={d: False for d in Dimension},
                    dimension_verdicts={d: f"Error: {str(e)}" for d in Dimension},
                    weighted_score=0.0,
                    passed=False,
                )
            )
            complexity_results[tc.complexity]["total"] += 1

    # Calculate final metrics
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r.passed)
    pass_rate = passed_cases / total_cases if total_cases > 0 else 0.0

    dimension_pass_rates = {}
    for dim in Dimension:
        total = dimension_totals[dim]
        passed = dimension_passes[dim]
        dimension_pass_rates[dim.value] = passed / total if total > 0 else 0.0

    # Format complexity results
    complexity_summary = {}
    for complexity, data in complexity_results.items():
        total = data["total"]
        passed = data["passed"]
        complexity_summary[complexity] = {
            "passed": passed,
            "total": total,
            "rate": passed / total if total > 0 else 0.0,
        }

    return EvaluationReport(
        total_cases=total_cases,
        passed_cases=passed_cases,
        pass_rate=pass_rate,
        dimension_pass_rates=dimension_pass_rates,
        by_complexity=complexity_summary,
        results=results,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def print_report(report: EvaluationReport) -> None:
    """Print a formatted evaluation report to console."""
    print("\n" + "=" * 60)
    print("SCRIPTURE RAG EVALUATION REPORT")
    print("=" * 60)
    print(f"Timestamp: {report.timestamp}")
    print(f"\nOverall: {report.passed_cases}/{report.total_cases} passed ({report.pass_rate:.1%})")

    print("\n--- By Dimension ---")
    for dim, rate in sorted(report.dimension_pass_rates.items()):
        status = "OK" if rate >= 0.75 else "NEEDS WORK"
        print(f"  {dim}: {rate:.1%} [{status}]")

    print("\n--- By Complexity ---")
    for complexity, data in report.by_complexity.items():
        print(f"  {complexity}: {data['passed']}/{data['total']} ({data['rate']:.1%})")

    print("\n--- Failed Cases ---")
    for result in report.results:
        if not result.passed:
            print(f"\n  [{result.test_case_id}] {result.question[:60]}...")
            print(f"    Score: {result.weighted_score:.2f}")
            for dim, verdict in result.dimension_verdicts.items():
                if not result.dimension_results[dim]:
                    print(f"    - {dim.value}: {verdict[:80]}")

    print("\n" + "=" * 60)
