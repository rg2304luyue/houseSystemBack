"""Versioned retrieval and answer-contract evaluation for the rental RAG."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
from time import perf_counter
from typing import Any, Iterable, Sequence

from app.services.query_router import route_query
from core.rag.retrieval_service import RagRetrievalService
from core.rag.types import RetrievedChunk


_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def reciprocal_rank(ranked_values: Sequence[str], relevant_values: Iterable[str]) -> float:
    relevant = {value.casefold() for value in relevant_values}
    for rank, value in enumerate(ranked_values, start=1):
        if value.casefold() in relevant:
            return 1.0 / rank
    return 0.0


def recall_at_k(ranked_values: Sequence[str], relevant_values: Iterable[str], k: int) -> float:
    relevant = {value.casefold() for value in relevant_values}
    if not relevant:
        return 0.0
    found = {value.casefold() for value in ranked_values[:k]} & relevant
    return len(found) / len(relevant)


def _source_key(chunk: RetrievedChunk) -> str:
    return chunk.source.casefold()


def _matched_source_keys(chunks: Sequence[RetrievedChunk], expected_sources: Sequence[str]) -> list[str]:
    matched: list[str] = []
    for chunk in chunks:
        source = _source_key(chunk)
        expected = next((item for item in expected_sources if item.casefold() in source), None)
        matched.append(expected.casefold() if expected else source)
    return matched


def evaluate_answer_contract(
    answer: str,
    evidence: Sequence[str],
    *,
    citation_required: bool = True,
    required_facts: Sequence[dict[str, Any]] = (),
    forbidden_claims: Sequence[str] = (),
) -> dict[str, float]:
    """Score citation bounds, cited evidence support, and annotated facts.

    Facts use ``answer_terms`` and ``evidence_terms`` aliases. This intentionally
    avoids a second LLM judge so release checks remain deterministic.
    """

    citations = [int(value) for value in _CITATION_PATTERN.findall(answer)]
    valid_citations = bool(citations) if citation_required else True
    valid_citations = valid_citations and all(1 <= value <= len(evidence) for value in citations)
    cited_text = "\n".join(evidence[index - 1] for index in citations if 1 <= index <= len(evidence))

    mentioned = supported = 0
    for fact in required_facts:
        answer_terms = [str(value) for value in fact.get("answer_terms", [])]
        evidence_terms = [str(value) for value in fact.get("evidence_terms", answer_terms)]
        is_mentioned = bool(answer_terms) and any(value in answer for value in answer_terms)
        if is_mentioned:
            mentioned += 1
            if valid_citations and any(value in cited_text for value in evidence_terms):
                supported += 1

    forbidden_ok = not any(value and value in answer for value in forbidden_claims)
    if required_facts:
        fact_consistency = supported / len(required_facts)
        faithfulness = supported / mentioned if mentioned else 0.0
    else:
        fact_consistency = 1.0 if forbidden_ok else 0.0
        faithfulness = 1.0 if valid_citations else 0.0
    if not forbidden_ok:
        fact_consistency = 0.0
    return {
        "citation_validity": float(valid_citations),
        "citation_faithfulness": round(faithfulness, 4),
        "fact_consistency": round(fact_consistency, 4),
    }


def _load_cases(dataset_path: Path) -> tuple[int, list[dict[str, Any]]]:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return 1, payload
    if not isinstance(payload, dict) or not isinstance(payload.get("cases"), list):
        raise ValueError("evaluation dataset must be a case list or a schema-v2 object")
    return int(payload.get("schema_version", 2)), payload["cases"]


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def evaluate(dataset_path: Path) -> dict[str, object]:
    schema_version, cases = _load_cases(dataset_path)
    service = RagRetrievalService()
    route_hits = 0
    reciprocal_ranks: list[float] = []
    recalls: dict[int, list[float]] = {1: [], 3: [], 6: []}
    refusal_correct = refusal_total = 0
    answerable_grounded = answerable_total = 0
    answer_scores: list[dict[str, float]] = []
    latencies: list[float] = []
    details: list[dict[str, Any]] = []
    threshold = float(service.config.get("relevance_score_threshold", 0.58))

    for case in cases:
        expected_route = str(case.get("expected_route", "general"))
        predicted_route = route_query(str(case["query"])).value
        route_hit = predicted_route == expected_route
        route_hits += int(route_hit)
        detail: dict[str, Any] = {
            "id": case.get("id"),
            "route": predicted_route,
            "route_hit": route_hit,
        }

        if case.get("evaluate_retrieval", False):
            knowledge_types = tuple(str(value) for value in case.get("knowledge_types", [])) or None
            started = perf_counter()
            chunks = service.vector_store.search(
                str(case["query"]), top_k=6, score_threshold=-1.0,
                knowledge_types=knowledge_types,
            )
            latencies.append((perf_counter() - started) * 1000)
            accepted = [chunk for chunk in chunks if chunk.score >= threshold]
            expected_sources = [str(value) for value in case.get("relevant_sources", [])]
            ranked = _matched_source_keys(chunks, expected_sources)
            relevant = [value.casefold() for value in expected_sources]
            if case.get("answerable", False) and relevant:
                answerable_total += 1
                answerable_grounded += int(bool(accepted))
                rr = reciprocal_rank(ranked, relevant)
                reciprocal_ranks.append(rr)
                detail["reciprocal_rank"] = round(rr, 4)
                for k in recalls:
                    recalls[k].append(recall_at_k(ranked, relevant, k))
            elif not case.get("answerable", False):
                refusal_total += 1
                refusal_correct += int(not accepted)
            detail.update({
                "grounded": bool(accepted),
                "sources": [chunk.source for chunk in chunks],
                "scores": [chunk.score for chunk in chunks],
            })

            if isinstance(case.get("answer"), str):
                contract = evaluate_answer_contract(
                    case["answer"],
                    [chunk.content for chunk in accepted],
                    citation_required=bool(case.get("citation_required", True)),
                    required_facts=case.get("required_facts", []),
                    forbidden_claims=case.get("forbidden_claims", []),
                )
                answer_scores.append(contract)
                detail.update(contract)
        details.append(detail)

    def mean(values: Sequence[float]) -> float | None:
        return round(sum(values) / len(values), 4) if values else None

    metrics: dict[str, object] = {
        "schema_version": schema_version,
        "cases": len(cases),
        "route_accuracy": round(route_hits / len(cases), 4) if cases else None,
        "mrr": mean(reciprocal_ranks),
        "recall_at_1": mean(recalls[1]),
        "recall_at_3": mean(recalls[3]),
        "recall_at_6": mean(recalls[6]),
        "refusal_accuracy": round(refusal_correct / refusal_total, 4) if refusal_total else None,
        "answerable_grounding_accuracy": round(answerable_grounded / answerable_total, 4) if answerable_total else None,
        "citation_validity": mean([item["citation_validity"] for item in answer_scores]),
        "citation_faithfulness": mean([item["citation_faithfulness"] for item in answer_scores]),
        "fact_consistency": mean([item["fact_consistency"] for item in answer_scores]),
        "evaluated_answer_cases": len(answer_scores),
        "answer_evaluation_mode": "annotated_contract_fixtures_not_live_agent",
        "mean_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "p95_latency_ms": round(_percentile(latencies, 0.95), 2),
        "details": details,
    }
    # Backward-compatible alias used by the previous release check.
    metrics["source_recall_at_k"] = metrics["recall_at_6"]
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate rental routing and retrieval")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).parents[1] / "evals" / "rag_eval.json")
    parser.add_argument("--min-mrr", type=float, default=0.75)
    parser.add_argument("--min-recall-at-3", type=float, default=0.85)
    parser.add_argument("--min-route-accuracy", type=float, default=0.9)
    parser.add_argument("--min-refusal-accuracy", type=float, default=0.8)
    parser.add_argument("--min-answerable-grounding", type=float, default=0.85)
    args = parser.parse_args()
    metrics = evaluate(args.dataset)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    legacy_recall = metrics.get("source_recall_at_k")
    required = (
        (metrics.get("mrr", legacy_recall), args.min_mrr),
        (metrics.get("recall_at_3", legacy_recall), args.min_recall_at_3),
        (metrics.get("route_accuracy", 1.0), args.min_route_accuracy),
        (metrics["refusal_accuracy"], args.min_refusal_accuracy),
        (metrics.get("answerable_grounding_accuracy", 1.0), args.min_answerable_grounding),
    )
    return int(any(value is None or value < minimum for value, minimum in required))


if __name__ == "__main__":
    raise SystemExit(main())
