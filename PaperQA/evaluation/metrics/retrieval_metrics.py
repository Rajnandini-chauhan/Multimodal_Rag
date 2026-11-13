"""Evaluation metrics for RAG retrieval recall, citation precision/recall, and grounding."""

from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class MetricResult:
    test_id: str
    page_recall: float
    page_precision: float
    citation_f1: float
    figure_recall: float
    table_recall: float
    grounding_score: float
    latency_seconds: float
    metadata: dict = field(default_factory=dict)


def compute_precision_recall_f1(
    actual: Sequence[int], expected: Sequence[int]
) -> tuple[float, float, float]:
    """Calculate precision, recall, and F1 score for integer sets (e.g., page/figure numbers)."""
    act_set = set(actual)
    exp_set = set(expected)

    if not exp_set:
        # If no sources were expected, precision is 1.0 if none returned, else 0.0
        return (1.0 if not act_set else 0.5, 1.0, 1.0)

    if not act_set:
        return (0.0, 0.0, 0.0)

    true_positives = len(act_set.intersection(exp_set))
    precision = true_positives / len(act_set)
    recall = true_positives / len(exp_set)

    f1 = 0.0
    if precision + recall > 0:
        f1 = (2 * precision * recall) / (precision + recall)

    return (round(precision, 4), round(recall, 4), round(f1, 4))


def compute_keyword_grounding_score(answer: str, keywords: Sequence[str]) -> float:
    """Measure the percentage of ground-truth domain keywords present in the generated answer."""
    if not keywords:
        return 1.0
    if not answer:
        return 0.0

    lower_ans = answer.lower()
    matches = sum(1 for kw in keywords if kw.lower() in lower_ans)
    return round(matches / len(keywords), 4)


def aggregate_metrics(results: list[MetricResult]) -> dict:
    """Compute dataset-level average metrics."""
    if not results:
        return {}

    n = len(results)
    avg_page_recall = sum(r.page_recall for r in results) / n
    avg_page_precision = sum(r.page_precision for r in results) / n
    avg_citation_f1 = sum(r.citation_f1 for r in results) / n
    avg_fig_recall = sum(r.figure_recall for r in results) / n
    avg_tab_recall = sum(r.table_recall for r in results) / n
    avg_grounding = sum(r.grounding_score for r in results) / n
    avg_latency = sum(r.latency_seconds for r in results) / n

    return {
        "total_test_cases": n,
        "mean_page_recall": round(avg_page_recall, 4),
        "mean_page_precision": round(avg_page_precision, 4),
        "mean_citation_f1": round(avg_citation_f1, 4),
        "mean_figure_recall": round(avg_fig_recall, 4),
        "mean_table_recall": round(avg_tab_recall, 4),
        "mean_grounding_score": round(avg_grounding, 4),
        "mean_latency_seconds": round(avg_latency, 4),
    }
