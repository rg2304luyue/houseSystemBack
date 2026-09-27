# Production RAG operations

## Assistant response behavior (2026-09-26)

The assistant now retains naturally phrased SQL answers after deterministic
query/row checks and a bounded semantic review. Knowledge answers keep a
deterministic extractive fast path; faithful paraphrases can pass a separate
JSON-only model review. Review failure falls back to source excerpts or public
listing cards, not an instruction for the user to repeatedly rephrase.
Model review is not a proof of factual correctness: regression and human review
remain necessary. A review adds one model invocation (with the existing provider
timeout/retry policy), so latency and cost can increase.

RAG drafts are not sent as public tokens before validation; progress events and
the final validated response remain available. General conversation retains
token streaming. Combined listing/knowledge responses are reviewed against both
typed evidence sources. Listing references must remain parseable for follow-ups.

An approximate rental budget currently means +/-10%, disclosed in the search
instructions; an explicit upper bound takes precedence. Relative changes such
as "贵一点" ask for a new upper bound instead of inventing one. "换一批" excludes
IDs from the latest displayed listing turn, not every historical recommendation.
No new database schema, environment variables, vector index or frontend API is
required. Restart the backend after deployment to reload cached agent prompts.

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
The current relevance threshold is calibrated to `0.50`; re-evaluate it after
changing the model, source documents, or chunking strategy.

The manifest records each source hash, deterministic chunk IDs, update state,
and a monotonically increasing `generation`. Before the first Chroma mutation,
incremental sync writes `state=updating`; retrieval fails closed until the
manifest returns to `ready`. A sync that finds an interrupted `updating` or
`rebuilding` state automatically performs a full rebuild. Search verifies that
the generation is unchanged before returning evidence, so a query cannot
silently span an index update. Embedding or chunking configuration drift still
requires an explicit `--rebuild`.

Keep only one local indexing process active. A missing or unexpectedly empty
knowledge directory fails closed; intentional deletion of every source requires
the explicit `allow_empty_sync` configuration and should be reviewed separately.

If an update fails, the manifest remains incomplete and API retrieval is
blocked. Fix the upstream error and run normal sync; it will recover through a
full rebuild. `--rebuild` remains available for an explicit operator action.
Back up `core/core/chroma_db` and `core/rag_state` together before a rebuild so
they can be restored consistently.

Current inventory, prices, and availability belong to SQL. Policies and rental
guides belong to RAG. Public listing snapshots are tagged
`knowledge_type=historical_snapshot`, `is_current=false`, and include their
collection date; they must never be presented as currently available inventory.
`app.services.query_router.route_query` supplies the deterministic boundary for
the agent integration.

The agent tool returns JSON evidence: `grounded`, relevance score, source,
section/page, source URL, and collection date. When `grounded` is false, the
agent must state that the knowledge base has insufficient evidence. Retrieval
logs contain a query hash, counts, threshold, and latency—not the raw question.

The schema-v2 evaluation set contains 60 routing, historical retrieval,
refusal, mixed, and edge cases. Release checks report MRR, Recall@1/3/6, route
accuracy, refusal accuracy, and optional deterministic citation/fact scores
when an evaluated answer is supplied. Tune the relevance threshold using this
set. The release check also requires answerable queries to remain grounded, so
raising the threshold cannot improve refusal accuracy by silently refusing valid
questions. Consider BM25 only if the exact-keyword slice has Recall@3 below 0.90;
consider a reranker only when Recall@6 is healthy but MRR is below 0.75.

Citation faithfulness and fact consistency currently validate six annotated,
deterministic contract fixtures; they do not call DeepSeek and must not be quoted
as live-agent accuracy. A production release should additionally run a separately
versioned end-to-end answer set (with frozen outputs or a reviewed model judge).

## AI request recovery

The main SSE endpoint persists `running`, `retry_wait`, `completed`, `failed`,
and `cancelled` states. `blocked` is intentionally not a runtime state: it means
manual/external input is required and this service currently has no such workflow.
`partial` is also omitted because the API stores only a verified final answer, not
durable partial output. A retryable provider failure becomes `retry_wait`; an
exhausted or permanent failure becomes `failed`.

Each running request owns a random lease token, heartbeat timestamp and expiry.
Heartbeats extend the lease while graph events arrive. Startup and every new stream
submission scan expired leases: cancelled work becomes `cancelled`, otherwise it
becomes immediately reclaimable `retry_wait`. Recovery does not run a background
queue: the client checks `GET /chat-ai/runs/{request_id}` and resubmits the same
message and `request_id` when `next_retry_at` is due. Reclaim uses the original user message
and history cutoff, so it does not duplicate or absorb later messages. Closing an
SSE consumer records `CLIENT_DISCONNECTED`; terminal writes require the current
lease token so an old worker cannot overwrite a newer attempt.

DeepSeek uses explicit 5-second connect and 45-second read timeouts. DeepSeek and
DashScope each allow at most three physical attempts with full-jitter exponential
backoff (base 0.5 seconds, cap 8 seconds), process-local concurrency limits and a
five-failure/30-second circuit breaker. Agent admission is non-blocking: excess work
returns HTTP 429 with `Retry-After` instead of occupying all worker threads. These
limits are process-local, so the documented deployment model is one Uvicorn worker;
a multi-worker deployment needs a shared Redis-backed limiter and breaker.

## Reviewed failure feedback

Authenticated users may submit one failure category and comment for their own run.
Phone numbers, identity numbers, email addresses and token-like secrets are removed
before storage. Feedback remains `pending` until an administrator accepts or rejects
it; it is never inserted into prompts or the vector index automatically. Export only
accepted cases for human inspection:

```powershell
python -m core.rag.export_feedback --output core/evals/reviewed_feedback.json
```

Merge reviewed cases into the main evaluation set only after adding expected route,
source annotations and a regression assertion. This makes failure memory improve
future releases without turning arbitrary user text into executable knowledge.
