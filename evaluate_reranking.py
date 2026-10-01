"""Reproduce Exercise 3.5 from saved retrieval traces without new LLM calls."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path

from evaluate_answers import load_evaluation_inputs
from template import RAGASEvaluator, rerank_by_overlap


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, default=Path("golden_dataset.json"))
    parser.add_argument(
        "--actual", type=Path, default=Path("artifacts/actual_answers.json")
    )
    args = parser.parse_args()

    qa_pairs, _ = load_evaluation_inputs(args.golden, args.actual)
    evaluator = RAGASEvaluator()
    totals = [0.0] * 4
    print(
        "| ID | Recall before | Recall after | Precision before | "
        "Precision after | Delta Precision |"
    )
    print("|---|---:|---:|---:|---:|---:|")
    for pair in qa_pairs:
        before = pair.retrieved_contexts
        after = rerank_by_overlap(before, pair.question)
        if Counter(before) != Counter(after):
            raise ValueError(f"Reranker changed the retrieved set: {pair.metadata['id']}")

        recall_before = evaluator.evaluate_context_recall(before, pair.expected_answer)
        recall_after = evaluator.evaluate_context_recall(after, pair.expected_answer)
        if not math.isclose(recall_before, recall_after, abs_tol=1e-12):
            raise ValueError(f"Recall changed after permutation: {pair.metadata['id']}")
        precision_before = evaluator.evaluate_context_precision(
            before, pair.expected_answer
        )
        precision_after = evaluator.evaluate_context_precision(
            after, pair.expected_answer
        )
        scores = (recall_before, recall_after, precision_before, precision_after)
        totals = [total + score for total, score in zip(totals, scores)]
        print(
            f"| {pair.metadata['id']} | {recall_before:.3f} | {recall_after:.3f} | "
            f"{precision_before:.3f} | {precision_after:.3f} | "
            f"{precision_after - precision_before:+.3f} |"
        )

    averages = [total / len(qa_pairs) for total in totals]
    print(
        f"| **Avg ({len(qa_pairs)} cases)** | **{averages[0]:.3f}** | "
        f"**{averages[1]:.3f}** | **{averages[2]:.3f}** | "
        f"**{averages[3]:.3f}** | **{averages[3] - averages[2]:+.3f}** |"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
