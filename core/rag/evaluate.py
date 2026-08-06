"""Small offline retrieval evaluation for release checks."""

import argparse
import json
from pathlib import Path
from time import perf_counter

from core.rag.retrieval_service import RagRetrievalService


def evaluate(dataset_path: Path) -> dict[str, object]:
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))
    service = RagRetrievalService()
    hits = answerable = refusal_correct = refusal_total = 0
    latencies = []
    details = []
    for case in cases:
        started = perf_counter()
        result = service.retrieve(case["query"])
        latencies.append((perf_counter() - started) * 1000)
        expected = case.get("expected_source")
        source_hit = bool(expected and any(expected.casefold() in chunk.source.casefold() for chunk in result.chunks))
        if case["answerable"]:
            answerable += 1
            hits += int(source_hit)
        else:
            refusal_total += 1
            refusal_correct += int(not result.grounded)
        details.append({"query": case["query"], "grounded": result.grounded, "source_hit": source_hit})
    return {
        "cases": len(cases),
        "source_recall_at_k": round(hits / answerable, 4) if answerable else None,
        "refusal_accuracy": round(refusal_correct / refusal_total, 4) if refusal_total else None,
        "mean_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "details": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate rental knowledge retrieval")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).parents[1] / "evals" / "rag_eval.json")
    parser.add_argument("--min-source-recall", type=float, default=0.75)
    parser.add_argument("--min-refusal-accuracy", type=float, default=0.8)
    args = parser.parse_args()
    metrics = evaluate(args.dataset)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    recall = metrics["source_recall_at_k"]
    refusal = metrics["refusal_accuracy"]
    return int(recall is None or refusal is None or recall < args.min_source_recall
               or refusal < args.min_refusal_accuracy)


if __name__ == "__main__":
    raise SystemExit(main())
