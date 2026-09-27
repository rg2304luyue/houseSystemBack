"""Export administrator-approved, sanitized failures as evaluation candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.db.session import SessionLocal
from app.models.rag_feedback import RAGFailureCase


def approved_cases() -> list[dict[str, object]]:
    with SessionLocal() as db:
        rows = db.query(RAGFailureCase).filter(
            RAGFailureCase.review_status == "accepted"
        ).order_by(RAGFailureCase.id.asc()).all()
        cases = []
        for row in rows:
            route = row.expected_route or row.route or "general"
            sources = list(row.expected_sources or [])
            retrieval_route = route in {"rag", "historical_snapshot"}
            cases.append({
                "id": f"feedback-{row.id}",
                "query": row.sanitized_query or "",
                "expected_route": route,
                "evaluate_retrieval": retrieval_route,
                "answerable": bool(sources),
                "relevant_sources": sources,
                "citation_required": bool(sources),
                "tags": ["reviewed-feedback", row.failure_type],
            })
        return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Export reviewed RAG failure cases")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = {"schema_version": 2, "cases": approved_cases()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"exported": len(payload["cases"]), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
