"""Versioned Chroma indexing and scored retrieval for rental knowledge."""

from __future__ import annotations
import hashlib
import json
import logging
import os
from pathlib import Path
from threading import RLock
from time import perf_counter
from typing import Any
from uuid import uuid4
from filelock import FileLock
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.agent_model.factor import get_embedding_model
from core.agent_utils.config_handler import chroma_config
from core.agent_utils.path_tool import get_abs_path
from app.core.config import settings
from core.rag.knowledge_files import discover_sources, file_sha256, load_source
from core.rag.types import RetrievedChunk, SyncReport

logger = logging.getLogger(__name__)
_MANIFEST_VERSION = 2
_PARSER_SCHEMA_VERSION = 3
_INCOMPLETE_STATES = {"updating", "rebuilding"}


class VectorStoreServiceV2:
    def __init__(self, *, embedding_model: Any | None = None, vector_store: Any | None = None,
                 config: dict[str, Any] | None = None, data_path: str | Path | None = None,
                 manifest_path: str | Path | None = None) -> None:
        self.config = dict(chroma_config if config is None else config)
        self.data_path = Path(data_path if data_path is not None else get_abs_path(self.config["data_path"])).resolve()
        self.manifest_path = Path(manifest_path if manifest_path is not None else get_abs_path(self.config.get("manifest_path", "index_manifest.json"))).resolve()
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_store = vector_store if vector_store is not None else Chroma(
            collection_name=self.config["collection_name"],
            embedding_function=embedding_model or get_embedding_model(),
            persist_directory=get_abs_path(self.config["persist_directory"]),
            collection_metadata={"hnsw:space": "cosine"},
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(self.config.get("chunk_size", 500)),
            chunk_overlap=int(self.config.get("chunk_overlap", 60)),
            separators=self.config.get("separators_safe") or self.config.get("separators_v2") or self.config.get("separators") or ["\n\n", "\n", "。", "！", "？", ".", " ", ""],
            length_function=len,
        )
        self._sync_lock = RLock()

    def _index_signature(self) -> str:
        payload = {
            "embedding_model": self.config.get("embedding_model") or settings.AI_EMBEDDING_MODEL,
            "chunk_size": int(self.config.get("chunk_size", 500)),
            "chunk_overlap": int(self.config.get("chunk_overlap", 60)),
            "separators": self.config.get("separators_safe") or self.config.get("separators_v2") or self.config.get("separators"),
            "parser_schema_version": _PARSER_SCHEMA_VERSION,
        }
        return self._digest(json.dumps(payload, ensure_ascii=False, sort_keys=True))

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _document_id(self, path: Path) -> str:
        return self._digest(path.resolve().relative_to(self.data_path).as_posix().casefold())

    def _empty_manifest(self) -> dict[str, Any]:
        return {
            "version": _MANIFEST_VERSION,
            "collection": self.config["collection_name"],
            "index_signature": self._index_signature(),
            "state": "ready",
            "generation": 0,
            "documents": {},
        }

    def _read_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return self._empty_manifest()
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"RAG index manifest is unreadable: {self.manifest_path}") from error

    def _load_manifest(self) -> dict[str, Any]:
        manifest = self._read_manifest()
        if manifest.get("version") != _MANIFEST_VERSION or not isinstance(manifest.get("documents"), dict):
            raise RuntimeError("RAG index manifest version is unsupported; run a full rebuild")
        if manifest.get("collection") != self.config["collection_name"]:
            raise RuntimeError("RAG index manifest belongs to another collection; run a full rebuild")
        if manifest.get("index_signature") != self._index_signature():
            raise RuntimeError("RAG embedding or chunking configuration changed; run a full rebuild")
        if manifest.get("state", "ready") != "ready":
            raise RuntimeError("RAG index has an incomplete rebuild or update; run sync to recover")
        generation = manifest.get("generation", 0)
        if not isinstance(generation, int) or generation < 0:
            raise RuntimeError("RAG index manifest generation is invalid; run a full rebuild")
        return manifest

    def _write_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_suffix(self.manifest_path.suffix + ".tmp")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.manifest_path)

    def _source_files(self) -> tuple[Path, ...]:
        if not self.data_path.is_dir():
            raise RuntimeError(f"Knowledge data directory is unavailable: {self.data_path}")
        return discover_sources(self.data_path, tuple(self.config.get("allow_knowledge_file_type", ["txt", "pdf"])),
                                recursive=bool(self.config.get("recursive", True)))

    def _chunks_for_file(self, path: Path, document_id: str, content_hash: str) -> tuple[list[Document], list[str]]:
        source = path.relative_to(self.data_path).as_posix()
        chunks: list[Document] = []
        chunk_ids: list[str] = []
        chunk_index = 0
        for loaded in load_source(path):
            for chunk in self.splitter.split_documents([loaded]):
                content = chunk.page_content.strip()
                if not content:
                    continue
                chunk_id = self._digest(f"{document_id}:{content_hash}:{chunk_index}")
                metadata = {key: value for key, value in chunk.metadata.items()
                            if value is not None and isinstance(value, (str, int, float, bool))}
                metadata.update({"chunk_id": chunk_id, "chunk_index": chunk_index,
                                 "content_hash": content_hash, "document_id": document_id, "source": source})
                chunks.append(Document(page_content=content, metadata=metadata))
                chunk_ids.append(chunk_id)
                chunk_index += 1
        return chunks, chunk_ids

    def sync_documents(self, *, rebuild: bool = False) -> SyncReport:
        with self._sync_lock, FileLock(str(self.manifest_path) + ".lock", timeout=0):
            started = perf_counter()
            source_files = self._source_files()
            if not source_files and not bool(self.config.get("allow_empty_sync", False)):
                raise RuntimeError("Knowledge data directory contains no supported files; refusing destructive sync")
            manifest_exists = self.manifest_path.exists()
            raw_manifest = self._read_manifest()
            if not manifest_exists:
                # Without a manifest there is no safe way to identify and delete
                # vectors left in an existing persistent collection.
                rebuild = True
            if raw_manifest.get("state") in _INCOMPLETE_STATES:
                logger.warning("rag_index_recovery state=%s action=full_rebuild", raw_manifest.get("state"))
                rebuild = True
            if rebuild:
                previous_generation = raw_manifest.get("generation", 0)
                if not isinstance(previous_generation, int) or previous_generation < 0:
                    previous_generation = 0
                manifest = self._empty_manifest()
                manifest.update({
                    "state": "rebuilding",
                    "generation": previous_generation,
                    "update_id": str(uuid4()),
                })
            else:
                manifest = self._load_manifest()
            documents: dict[str, Any] = manifest["documents"]
            seen: set[str] = set()
            indexed = skipped = removed_documents = written = removed_chunks = 0
            planned_updates: list[tuple[Path, str, str, dict[str, Any] | None, list[Document], list[str]]] = []
            for path in source_files:
                document_id = self._document_id(path)
                seen.add(document_id)
                content_hash = file_sha256(path)
                previous = documents.get(document_id)
                if not rebuild and previous and previous.get("content_hash") == content_hash:
                    skipped += 1
                    continue
                chunks, chunk_ids = self._chunks_for_file(path, document_id, content_hash)
                if not chunks:
                    raise RuntimeError(f"Knowledge source produced no chunks: {path}")
                planned_updates.append((path, document_id, content_hash, previous, chunks, chunk_ids))

            stale_document_ids = sorted(set(documents) - seen) if not rebuild else []
            if not rebuild and not planned_updates and not stale_document_ids:
                logger.info(
                    "rag_index_sync indexed=0 skipped=%s removed_documents=0 written_chunks=0 removed_chunks=0 duration_ms=%s",
                    skipped, round((perf_counter() - started) * 1000, 2),
                )
                return SyncReport(skipped_documents=skipped)

            manifest["state"] = "rebuilding" if rebuild else "updating"
            manifest["update_id"] = str(uuid4())
            self._write_manifest(manifest)
            if rebuild:
                self.vector_store.reset_collection()
                documents.clear()

            for path, document_id, content_hash, previous, chunks, chunk_ids in planned_updates:
                self.vector_store.add_documents(chunks, ids=chunk_ids)
                obsolete_ids = [] if rebuild else sorted(
                    set((previous or {}).get("chunk_ids", [])) - set(chunk_ids)
                )
                if obsolete_ids:
                    self.vector_store.delete(ids=obsolete_ids)
                    removed_chunks += len(obsolete_ids)
                documents[document_id] = {"chunk_ids": chunk_ids, "content_hash": content_hash,
                                          "source": path.relative_to(self.data_path).as_posix()}
                indexed += 1
                written += len(chunk_ids)
            for document_id in stale_document_ids:
                stale_ids = list(documents[document_id].get("chunk_ids", []))
                if stale_ids:
                    self.vector_store.delete(ids=stale_ids)
                    removed_chunks += len(stale_ids)
                del documents[document_id]
                removed_documents += 1
            manifest["state"] = "ready"
            manifest["generation"] = int(manifest.get("generation", 0)) + 1
            manifest.pop("update_id", None)
            self._write_manifest(manifest)
            logger.info("rag_index_sync indexed=%s skipped=%s removed_documents=%s written_chunks=%s removed_chunks=%s duration_ms=%s",
                        indexed, skipped, removed_documents, written, removed_chunks,
                        round((perf_counter() - started) * 1000, 2))
            return SyncReport(indexed, skipped, removed_documents, written, removed_chunks)

    def search(self, query: str, *, top_k: int | None = None,
               score_threshold: float | None = None,
               knowledge_types: tuple[str, ...] | None = None) -> list[RetrievedChunk]:
        before = self._load_manifest()
        cleaned_query = query.strip()[:1000]
        if not cleaned_query:
            return []
        safe_k = max(1, min(int(top_k or self.config.get("retrieval_k", 6)), 20))
        threshold = float(self.config.get("relevance_score_threshold", 0.35)
                          if score_threshold is None else score_threshold)
        started = perf_counter()
        search_kwargs: dict[str, Any] = {"k": safe_k}
        normalized_types = tuple(sorted({value.strip() for value in (knowledge_types or ()) if value.strip()}))
        if len(normalized_types) == 1:
            search_kwargs["filter"] = {"knowledge_type": normalized_types[0]}
        elif normalized_types:
            search_kwargs["filter"] = {"knowledge_type": {"$in": list(normalized_types)}}
        results = self.vector_store.similarity_search_with_relevance_scores(cleaned_query, **search_kwargs)
        chunks: list[RetrievedChunk] = []
        for document, score in results:
            relevance = float(score)
            if relevance < threshold:
                continue
            metadata = document.metadata
            page = metadata.get("page")
            chunks.append(RetrievedChunk(
                chunk_id=str(metadata.get("chunk_id", "")), content=document.page_content,
                score=round(relevance, 6), source=str(metadata.get("source", "unknown")),
                page=int(page) + 1 if isinstance(page, int) else None,
                section=str(metadata["section"]) if metadata.get("section") else None,
                source_url=str(metadata["source_url"]) if metadata.get("source_url") else None,
                collected_at=str(metadata["collected_at"]) if metadata.get("collected_at") else None,
                document_id=str(metadata["document_id"]) if metadata.get("document_id") else None,
                knowledge_type=str(metadata["knowledge_type"]) if metadata.get("knowledge_type") else None,
                title=str(metadata["title"]) if metadata.get("title") else None,
                effective_at=str(metadata["effective_at"]) if metadata.get("effective_at") else None,
                jurisdiction=str(metadata["jurisdiction"]) if metadata.get("jurisdiction") else None,
                verification_status=str(metadata["verification_status"]) if metadata.get("verification_status") else None,
                is_current=bool(metadata["is_current"]) if "is_current" in metadata else None,
                house_num=str(metadata["house_num"]) if metadata.get("house_num") else None,
            ))
        after = self._load_manifest()
        if after.get("generation", 0) != before.get("generation", 0):
            raise RuntimeError("RAG index changed during search; retry the query")
        logger.info("rag_search query_hash=%s candidates=%s accepted=%s threshold=%s duration_ms=%s",
                    self._digest(cleaned_query)[:12], len(results), len(chunks), threshold,
                    round((perf_counter() - started) * 1000, 2))
        return chunks
