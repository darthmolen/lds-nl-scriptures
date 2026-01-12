"""Configuration for evaluation framework.

Environment variables:
- JUDGE_LLM_URL: vLLM endpoint (default: http://localhost:8004/v1)
- JUDGE_LLM_MODEL: Model name (default: auto-detect)
"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class EvaluationSettings:
    """Settings for the evaluation framework."""

    # Judge LLM settings
    judge_llm_url: str = "http://localhost:8004/v1"
    judge_llm_model: str | None = None  # Auto-detect from server

    # Evaluation thresholds
    pass_threshold: float = 0.75  # Overall pass rate threshold
    recall_at_5_threshold: float = 0.70
    recall_at_10_threshold: float = 0.80

    # Golden test set
    golden_test_path: str = "tests/evaluation/golden"


@lru_cache
def get_settings() -> EvaluationSettings:
    """Get evaluation settings from environment."""
    return EvaluationSettings(
        judge_llm_url=os.getenv("JUDGE_LLM_URL", "http://localhost:8004/v1"),
        judge_llm_model=os.getenv("JUDGE_LLM_MODEL"),
        pass_threshold=float(os.getenv("EVAL_PASS_THRESHOLD", "0.75")),
        recall_at_5_threshold=float(os.getenv("EVAL_RECALL_5_THRESHOLD", "0.70")),
        recall_at_10_threshold=float(os.getenv("EVAL_RECALL_10_THRESHOLD", "0.80")),
        golden_test_path=os.getenv(
            "EVAL_GOLDEN_PATH", "tests/evaluation/golden"
        ),
    )
