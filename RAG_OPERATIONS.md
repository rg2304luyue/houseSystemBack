# Production RAG operations

Rental knowledge files live in `core/data`. Indexing is an explicit deployment
step; the API process does not rebuild the index at startup.

```powershell
# Incremental, idempotent synchronization
python -m core.rag.indexer

# Required after changing the embedding model or chunking configuration
python -m core.rag.indexer --rebuild

# Retrieval regression metrics (requires the configured embedding API)
python -m core.rag.evaluate
```

The default embedding model is `qwen3.7-text-embedding` with its API-default
1024 dimensions. Changing `AI_EMBEDDING_MODEL` always requires `--rebuild`;
vectors from different model versions must never share one collection.
The current relevance threshold is calibrated to `0.58`; re-evaluate it after
changing the model, source documents, or chunking strategy.

The manifest records each source hash and deterministic chunk IDs. Changed
sources are added before obsolete chunks are removed. Deleted source files are
removed from Chroma during the next synchronization. Embedding or chunking
configuration drift fails closed and requires `--rebuild`.

Keep only one local indexing process active. A missing or unexpectedly empty
knowledge directory fails closed; intentional deletion of every source requires
the explicit `allow_empty_sync` configuration and should be reviewed separately.

If a rebuild fails, the manifest remains in `rebuilding` state and normal sync
or API retrieval must not be treated as healthy. Fix the upstream error and run
`python -m core.rag.indexer --rebuild` again. Back up `core/core/chroma_db` and
`core/rag_state` together before a rebuild so they can be restored consistently.

The agent tool returns JSON evidence: `grounded`, relevance score, source,
section/page, source URL, and collection date. When `grounded` is false, the
agent must state that the knowledge base has insufficient evidence. Retrieval
logs contain a query hash, counts, threshold, and latency—not the raw question.

Before release, run unit tests and record the offline evaluation metrics. Tune
the relevance threshold using the evaluation set; do not add hybrid retrieval
or reranking until measurements show that dense retrieval is insufficient.
