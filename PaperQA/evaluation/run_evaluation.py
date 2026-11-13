"""Automated Evaluation Runner for PaperQA RAG, Citation Accuracy, and Grounding.

Usage:
    python evaluation/run_evaluation.py [--paper-id <paper_id>] [--dataset <path>]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add backend and root directories to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(ROOT_DIR))

from app.database.session import SessionLocal
from app.models.paper import Paper
from app.services.qa import generate_answer, retrieve_relevant_content
from evaluation.metrics.retrieval_metrics import (
    MetricResult,
    aggregate_metrics,
    compute_keyword_grounding_score,
    compute_precision_recall_f1,
)


def resolve_target_paper_id(explicit_id: str | None) -> str:
    """Find explicit paper or an indexed paper in PostgreSQL."""
    if explicit_id:
        return explicit_id

    db = SessionLocal()
    try:
        from app.models.ingestion_job import IngestionJob, IngestionStatus

        # First check if the benchmark paper (Mental Health Assistant) is available
        benchmark_paper = (
            db.query(Paper)
            .filter(Paper.original_filename.ilike("%mental%"))
            .first()
        )
        if benchmark_paper:
            return str(benchmark_paper.id)

        # Fallback to any completed ingestion paper
        completed_job = (
            db.query(IngestionJob)
            .filter(IngestionJob.status == IngestionStatus.COMPLETED)
            .order_by(IngestionJob.created_at.desc())
            .first()
        )
        if completed_job and completed_job.paper_id:
            return str(completed_job.paper_id)

        paper = db.query(Paper).order_by(Paper.created_at.desc()).first()
        if not paper:
            raise RuntimeError(
                "No papers found in database. Please upload and index a paper first."
            )
        return str(paper.id)
    finally:
        db.close()


def run_benchmark(
    dataset_path: Path, paper_id: str, output_path: Path
) -> dict:
    """Run benchmark queries against PaperQA RAG and compile metrics."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    print("=" * 70)
    print("PaperQA Benchmark Evaluation Suite")
    print(f"Target Paper ID : {paper_id}")
    print(f"Test Cases      : {len(test_cases)}")
    print(f"Dataset         : {dataset_path.name}")
    print("=" * 70)

    results: list[MetricResult] = []
    detailed_outputs = []

    for idx, tc in enumerate(test_cases, 1):
        tc_id = tc["id"]
        question = tc["question"]
        expected_pages = tc.get("expected_pages", [])
        expected_figures = tc.get("expected_figures", [])
        expected_tables = tc.get("expected_tables", [])
        keywords = tc.get("ground_truth_keywords", [])

        print(f"\n[{idx}/{len(test_cases)}] Evaluating {tc_id}: '{question[:45]}...'")

        start_time = time.perf_counter()
        try:
            items = retrieve_relevant_content(paper_id, question)
            ans_result = generate_answer(question, items)
            latency = round(time.perf_counter() - start_time, 3)

            actual_pages = ans_result.sources or []
            actual_figures = ans_result.figures or []
            actual_tables = ans_result.tables or []
            answer_text = ans_result.answer or ""

            # Metrics
            page_prec, page_rec, page_f1 = compute_precision_recall_f1(
                actual_pages, expected_pages
            )
            _, fig_rec, _ = compute_precision_recall_f1(
                actual_figures, expected_figures
            )
            _, tab_rec, _ = compute_precision_recall_f1(
                actual_tables, expected_tables
            )
            grounding = compute_keyword_grounding_score(answer_text, keywords)

            res = MetricResult(
                test_id=tc_id,
                page_recall=page_rec,
                page_precision=page_prec,
                citation_f1=page_f1,
                figure_recall=fig_rec,
                table_recall=tab_rec,
                grounding_score=grounding,
                latency_seconds=latency,
                metadata={"category": tc.get("category", "general")},
            )
            results.append(res)

            detailed_outputs.append(
                {
                    "test_id": tc_id,
                    "question": question,
                    "category": tc.get("category"),
                    "latency_seconds": latency,
                    "answer_preview": answer_text[:120] + "...",
                    "actual_pages": actual_pages,
                    "expected_pages": expected_pages,
                    "actual_figures": actual_figures,
                    "expected_figures": expected_figures,
                    "actual_tables": actual_tables,
                    "expected_tables": expected_tables,
                    "metrics": {
                        "page_recall": page_rec,
                        "page_precision": page_prec,
                        "citation_f1": page_f1,
                        "figure_recall": fig_rec,
                        "table_recall": tab_rec,
                        "grounding_score": grounding,
                    },
                }
            )

            print(
                f"   -> Recall: {page_rec:.2f} | Precision: {page_prec:.2f} | "
                f"Grounding: {grounding:.2f} | Latency: {latency:.2f}s"
            )

        except Exception as exc:
            latency = round(time.perf_counter() - start_time, 3)
            print(f"   -> FAILED: {exc}")
            results.append(
                MetricResult(
                    test_id=tc_id,
                    page_recall=0.0,
                    page_precision=0.0,
                    citation_f1=0.0,
                    figure_recall=0.0,
                    table_recall=0.0,
                    grounding_score=0.0,
                    latency_seconds=latency,
                    metadata={"error": str(exc)},
                )
            )

    aggregates = aggregate_metrics(results)

    # Format report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "paper_id": paper_id,
        "summary": aggregates,
        "detailed_results": detailed_outputs,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY REPORT")
    print("=" * 70)
    for k, v in aggregates.items():
        print(f" {k:<25} : {v}")
    print(f"\nDetailed report saved to: {output_path}")
    print("=" * 70)

    return report


def main():
    parser = argparse.ArgumentParser(description="Run PaperQA Evaluation Benchmark")
    parser.add_argument("--paper-id", type=str, default=None, help="Paper UUID")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(__file__).parent / "datasets" / "benchmark_qa.json",
        help="Path to benchmark QA JSON dataset",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "reports" / "evaluation_report.json",
        help="Output report JSON path",
    )

    args = parser.parse_args()
    target_paper_id = resolve_target_paper_id(args.paper_id)
    run_benchmark(args.dataset, target_paper_id, args.output)


if __name__ == "__main__":
    main()
