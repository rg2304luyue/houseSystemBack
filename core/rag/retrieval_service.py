"""Retrieval-only RAG service; final generation belongs to the outer agent."""

from typing import Any
from core.agent_utils.config_handler import chroma_config
from core.rag.types import KnowledgeSearchResult, RetrievedChunk
from core.rag.vector_store_v2 import VectorStoreServiceV2


class RagRetrievalService:
    def __init__(self, vector_store: VectorStoreServiceV2 | None = None,
                 *, config: dict[str, Any] | None = None) -> None:
        self.config = dict(chroma_config if config is None else config)
        self.vector_store = vector_store if vector_store is not None else VectorStoreServiceV2(config=self.config)

    def retrieve(self, query: str) -> KnowledgeSearchResult:
        cleaned_query = query.strip()[:1000]
        if not cleaned_query:
            return KnowledgeSearchResult(query="", grounded=False)
        chunks = self.vector_store.search(cleaned_query)
        budget = min(max(1, int(self.config.get("max_context_chars", 8000))), 100_000)
        accepted: list[RetrievedChunk] = []
        used = 0
        for chunk in chunks:
            remaining = budget - used
            if remaining <= 0:
                break
            content = chunk.content[:remaining]
            if not content.strip():
                continue
            accepted.append(RetrievedChunk(
                chunk_id=chunk.chunk_id, content=content, score=chunk.score, source=chunk.source,
                page=chunk.page, section=chunk.section, source_url=chunk.source_url,
                collected_at=chunk.collected_at, document_id=chunk.document_id,
            ))
            used += len(content)
        return KnowledgeSearchResult(query=cleaned_query, grounded=bool(accepted), chunks=accepted)
