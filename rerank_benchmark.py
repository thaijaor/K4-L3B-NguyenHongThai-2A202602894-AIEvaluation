"""Measure Exercise 3.5 on saved traces without generating new answers."""

import json
from collections import Counter
from pathlib import Path

from evaluate_answers import load_evaluation_inputs
from template import RAGASEvaluator, rerank_by_overlap


def main() -> None:
    pairs, _ = load_evaluation_inputs(
        "golden_dataset.json", "artifacts/actual_answers.json"
    )
    evaluator = RAGASEvaluator()
    rows: list[dict[str, str | float]] = []
    for pair in pairs:
        before = pair.retrieved_contexts
        after = rerank_by_overlap(before, pair.question)
        assert Counter(before) == Counter(after), "Reranker changed chunk membership"
        recall_before = evaluator.evaluate_context_recall(before, pair.expected_answer)
        recall_after = evaluator.evaluate_context_recall(after, pair.expected_answer)
        assert recall_before == recall_after, "Reranker changed recall"
        precision_before = evaluator.evaluate_context_precision(before, pair.expected_answer)
        precision_after = evaluator.evaluate_context_precision(after, pair.expected_answer)
        rows.append({
            "id": pair.metadata["id"],
            "recall_before": recall_before,
            "recall_after": recall_after,
            "precision_before": precision_before,
            "precision_after": precision_after,
            "delta_precision": precision_after - precision_before,
        })
    artifact = {
        "method": "lexical overlap with question; no gold answer used for reranking",
        "source": "artifacts/actual_answers.json",
        "results": rows,
        "averages": {
            key: sum(float(row[key]) for row in rows) / len(rows)
            for key in rows[0] if key != "id"
        },
    }
    Path("artifacts/reranking_results.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(artifact["averages"], indent=2))


if __name__ == "__main__":
    main()
