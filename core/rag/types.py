"""Typed contracts shared by RAG indexing, retrieval, and agent tools."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    source: str
    page: int | None = None
    section: str | None = None
    source_url: str | None = None
    collected_at: str | None = None
    document_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class KnowledgeSearchResult:
    query: str
    grounded: bool
    chunks: list[RetrievedChunk] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "grounded": self.grounded,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }


@dataclass(frozen=True)
class SyncReport:
    indexed_documents: int = 0
    skipped_documents: int = 0
    removed_documents: int = 0
    written_chunks: int = 0
    removed_chunks: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)
