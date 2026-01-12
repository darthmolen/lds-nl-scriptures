"""Evaluation framework for Scripture Search RAG.

Uses local Qwen2 via vLLM as LLM-as-judge for quality assessment.
Includes retrieval recall measurement for search quality evaluation.
"""

from .judge import JudgeLLM, get_judge
from .rubrics import (
    Dimension,
    Rubric,
    get_rubric,
    get_all_rubrics,
    calculate_weighted_score,
)
from .config import EvaluationSettings, get_settings
from .retrieval import (
    RecallResult,
    RecallReport,
    RetrievalTestCase,
    calculate_recall,
    run_recall_evaluation,
    print_recall_report,
    load_retrieval_ground_truth,
    create_api_search_client,
    create_direct_search_client,
)

__all__ = [
    # Judge LLM
    "JudgeLLM",
    "get_judge",
    # Rubrics
    "Dimension",
    "Rubric",
    "get_rubric",
    "get_all_rubrics",
    "calculate_weighted_score",
    # Config
    "EvaluationSettings",
    "get_settings",
    # Retrieval evaluation
    "RecallResult",
    "RecallReport",
    "RetrievalTestCase",
    "calculate_recall",
    "run_recall_evaluation",
    "print_recall_report",
    "load_retrieval_ground_truth",
    "create_api_search_client",
    "create_direct_search_client",
]
