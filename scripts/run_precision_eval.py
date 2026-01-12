#!/usr/bin/env python3
"""Run retrieval precision evaluation with LLM-as-judge.

Usage:
    python scripts/run_precision_eval.py
    python scripts/run_precision_eval.py --verbose
"""

import argparse
import sys
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
)


@contextmanager
def session_factory():
    """Create database session context manager."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Run retrieval precision evaluation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed judgments")
    args = parser.parse_args()

    print("Creating search client...")
    search_client = create_direct_search_client(session_factory)

    print("Running precision evaluation (this will take a few minutes)...")
    print("Each test case requires 10 LLM judge calls.\n")

    report = run_precision_evaluation(search_client)

    print_precision_report(report, verbose=args.verbose)

    # Return exit code based on pass/fail
    sys.exit(0 if report.overall_pass else 1)


if __name__ == "__main__":
    main()
