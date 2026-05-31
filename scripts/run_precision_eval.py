#!/usr/bin/env python3
"""Run retrieval precision evaluation with LLM-as-judge.

Usage:
    python scripts/run_precision_eval.py
    python scripts/run_precision_eval.py --verbose
    python scripts/run_precision_eval.py --name "experiment_name"
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from contextlib import contextmanager
from src.db.config import SessionLocal
from src.evaluation.retrieval import (
    run_precision_evaluation,
    print_precision_report,
    create_direct_search_client,
    PrecisionReport,
)
from src.api.services.search import DEFAULT_VECTOR_WEIGHT, ENABLE_QUERY_EXPANSION


@contextmanager
def session_factory():
    """Create database session context manager."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_search_config() -> dict:
    """Get current search configuration variables.

    Returns:
        Dictionary of configuration variables and their current values.
    """
    return {
        "vector_weight": DEFAULT_VECTOR_WEIGHT,
        "text_weight": 1.0 - DEFAULT_VECTOR_WEIGHT,
        "query_expansion": ENABLE_QUERY_EXPANSION,
        "embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 1536,
        "index_type": "HNSW",
        "hnsw_m": 16,
        "hnsw_ef_construction": 64,
        "search_limit_multiplier": 3,
        "min_word_length": 3,
        "text_ranking_function": "ts_rank_cd",
    }


def format_report_to_text(
    report: PrecisionReport,
    config: dict,
    experiment_name: str = "",
    verbose: bool = False,
) -> str:
    """Format the precision report as text for file output.

    Args:
        report: PrecisionReport to format
        config: Search configuration dictionary
        experiment_name: Optional name for this experiment
        verbose: If True, include detailed judgments

    Returns:
        Formatted text report
    """
    lines = []
    lines.append("=" * 70)
    lines.append("RETRIEVAL PRECISION EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append(f"Timestamp: {report.timestamp}")
    if experiment_name:
        lines.append(f"Experiment: {experiment_name}")
    lines.append(f"Total test cases: {report.total_cases}")

    # Configuration section
    lines.append("")
    lines.append("--- Search Configuration ---")
    for key, value in config.items():
        lines.append(f"  {key}: {value}")

    # Overall metrics
    lines.append("")
    lines.append("--- Overall Metrics ---")
    p5_status = "PASS" if report.precision_at_5_pass else "FAIL"
    p10_status = "PASS" if report.precision_at_10_pass else "FAIL"

    lines.append(f"  Precision@5:  {report.precision_at_5:.1%} (threshold: 75%) [{p5_status}]")
    lines.append(f"  Precision@10: {report.precision_at_10:.1%} (threshold: 70%) [{p10_status}]")

    # By category
    lines.append("")
    lines.append("--- By Category ---")
    for category, metrics in sorted(report.by_category.items()):
        lines.append(f"  {category} (n={metrics['count']}):")
        lines.append(f"    Precision@5:  {metrics['precision_at_5']:.1%}")
        lines.append(f"    Precision@10: {metrics['precision_at_10']:.1%}")

    # Individual results
    lines.append("")
    lines.append("--- Test Case Results ---")
    for result in sorted(report.results, key=lambda x: x.precision_score):
        highly_rel = result.highly_relevant_count
        partial_rel = result.partially_relevant_count
        not_rel = result.not_relevant_count

        lines.append("")
        lines.append(f"  [{result.test_case_id}] {result.query[:50]}...")
        lines.append(f"    Precision@{result.k}: {result.precision_score:.1%}")
        lines.append(f"    Relevance: {highly_rel} high, {partial_rel} partial, {not_rel} not relevant")

        if verbose:
            lines.append(f"    Rubric: {result.relevance_rubric[:80]}...")
            lines.append("    Judgments:")
            for j in result.judgments:
                score_label = {3: "HIGH", 2: "PARTIAL", 1: "NOT REL"}[j.score]
                lines.append(f"      - [{score_label}] {j.reference}: {j.reasoning[:60]}...")

    # Summary
    lines.append("")
    lines.append("-" * 70)
    overall = "PASS" if report.overall_pass else "FAIL"
    lines.append(f"Overall Status: [{overall}]")
    lines.append("=" * 70)

    return "\n".join(lines)


def save_report(
    report: PrecisionReport,
    config: dict,
    experiment_name: str = "",
    verbose: bool = False,
) -> Path:
    """Save the precision report to a file.

    Args:
        report: PrecisionReport to save
        config: Search configuration dictionary
        experiment_name: Optional name for this experiment
        verbose: If True, include detailed judgments

    Returns:
        Path to the saved report file
    """
    # Create reports directory if needed
    reports_dir = project_root / "src" / "evaluation" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_part = f"_{experiment_name}" if experiment_name else ""
    filename = f"precision_eval_{timestamp}{name_part}.txt"
    filepath = reports_dir / filename

    # Format and save
    report_text = format_report_to_text(report, config, experiment_name, verbose)
    filepath.write_text(report_text)

    return filepath


def main():
    parser = argparse.ArgumentParser(description="Run retrieval precision evaluation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed judgments")
    parser.add_argument("--name", "-n", type=str, default="", help="Experiment name for the report")
    args = parser.parse_args()

    # Get current search configuration
    config = get_search_config()

    print("Creating search client...")
    search_client = create_direct_search_client(session_factory)

    print("Running precision evaluation (this will take a few minutes)...")
    print("Each test case requires 10 LLM judge calls.\n")

    print("Current configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()

    report = run_precision_evaluation(search_client)

    # Print to console
    print_precision_report(report, verbose=args.verbose)

    # Save to file
    report_path = save_report(report, config, args.name, args.verbose)
    print(f"\nReport saved to: {report_path}")

    # Return exit code based on pass/fail
    sys.exit(0 if report.overall_pass else 1)


if __name__ == "__main__":
    main()
