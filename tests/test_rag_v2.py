import json
from pathlib import Path
import sys

from filelock import FileLock, Timeout
from langchain_core.documents import Document
import pytest

from app.services.query_router import QueryRoute, route_query
from core.rag.evaluate import evaluate_answer_contract, recall_at_k, reciprocal_rank
from core.rag.knowledge_files import load_source
from core.rag.retrieval_service import RagRetrievalService
from core.rag.types import RetrievedChunk
from core.rag.vector_store_v2 import VectorStoreServiceV2


class FakeVectorStore:
    def __init__(self):
        self.documents = {}
        self.deleted = []
        self.reset_count = 0
        self.search_results = []

    def add_documents(self, documents, ids):
        self.documents.update(dict(zip(ids, documents)))

    def delete(self, ids):
        self.deleted.extend(ids)
        for chunk_id in ids:
            self.documents.pop(chunk_id, None)

    def reset_collection(self):
        self.documents.clear()
        self.reset_count += 1

    def similarity_search_with_relevance_scores(self, query, k, **kwargs):
        return self.search_results[:k]


def config():
    return {
        "collection_name": "rag_test_v2",
        "allow_knowledge_file_type": ["txt", "pdf"],
        "recursive": True,
        "chunk_size": 80,
        "chunk_overlap": 10,
        "separators_v2": ["\n\n", "\n", "。", "，", " ", ""],
        "retrieval_k": 6,
        "relevance_score_threshold": 0.5,
        "max_context_chars": 500,
        "embedding_model": "fake-embedding-v1",
    }


def service(tmp_path: Path, store: FakeVectorStore):
    data_path = tmp_path / "data"
    data_path.mkdir(exist_ok=True)
    return VectorStoreServiceV2(
        vector_store=store,
        config=config(),
        data_path=data_path,
        manifest_path=tmp_path / "manifest.json",
    )


def test_listing_txt_is_split_with_citation_metadata(tmp_path):
    source = tmp_path / "listing.txt"
    source.write_text(
        "采集日期：2026-08-06\n\n"
        "[房源 CS-PUBLIC-20260806-001]\n"
        "区域：岳麓区\n来源链接：https://example.test/1\n月租：1800元\n\n"
        "[房源 CS-PUBLIC-20260806-002]\n"
        "区域：天心区\n来源链接：https://example.test/2\n月租：2200元\n",
        encoding="utf-8",
    )

    documents = load_source(source)

    assert len(documents) == 2
    assert documents[0].metadata["house_num"] == "CS-PUBLIC-20260806-001"
    assert documents[0].metadata["source_url"] == "https://example.test/1"
    assert documents[0].metadata["collected_at"] == "2026-08-06"
    assert documents[0].metadata["knowledge_type"] == "historical_snapshot"
    assert documents[0].metadata["verification_status"] == "unverified_public_snapshot"
    assert documents[0].metadata["is_current"] is False
    assert documents[1].metadata["region"] == "天心区"


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("推荐岳麓区2000元左右当前可租的房源", QueryRoute.SQL),
        ("签租房合同有哪些注意事项？", QueryRoute.RAG),
        ("岳麓区有哪些公开房源快照？", QueryRoute.HISTORICAL_SNAPSHOT),
        ("当前房源和历史快照有什么差异？", QueryRoute.MIXED),
        ("长沙今天天气怎么样？", QueryRoute.WEATHER),
        ("当前长沙天气怎么样？", QueryRoute.WEATHER),
        ("你好", QueryRoute.GENERAL),
    ],
)
def test_query_router_enforces_data_source_boundaries(query, expected):
    assert route_query(query) is expected


def test_query_router_inherits_short_follow_up():
    assert route_query("这套？", ["推荐岳麓区当前可租的房源"]) is QueryRoute.SQL


def test_sync_is_idempotent_and_handles_update_and_delete(tmp_path):
    store = FakeVectorStore()
    rag = service(tmp_path, store)
    source = rag.data_path / "district.txt"
    source.write_text("第一版房源信息。" * 10, encoding="utf-8")

    first = rag.sync_documents()
    first_ids = set(store.documents)
    second = rag.sync_documents()
    source.write_text("第二版房源信息。" * 10, encoding="utf-8")
    updated = rag.sync_documents()
    updated_ids = set(store.documents)
    source.unlink()
    rag.config["allow_empty_sync"] = True
    removed = rag.sync_documents()

    assert first.indexed_documents == 1 and first.written_chunks > 0
    assert second.skipped_documents == 1 and second.written_chunks == 0
    assert updated.indexed_documents == 1
    assert first_ids.isdisjoint(updated_ids)
    assert first_ids.issubset(set(store.deleted))
    assert removed.removed_documents == 1
    assert not store.documents
    assert json.loads(rag.manifest_path.read_text(encoding="utf-8"))["documents"] == {}


def test_embedding_model_change_requires_rebuild_and_accepts_new_signature(tmp_path):
    store = FakeVectorStore()
    rag = service(tmp_path, store)
    (rag.data_path / "source.txt").write_text("可索引内容", encoding="utf-8")
    rag.sync_documents()
    resets_before_rebuild = store.reset_count
    changed = config()
    changed["embedding_model"] = "fake-embedding-v2"
    changed_service = VectorStoreServiceV2(
        vector_store=store, config=changed, data_path=rag.data_path,
        manifest_path=rag.manifest_path,
    )

    try:
        changed_service.sync_documents()
    except RuntimeError as error:
        assert "full rebuild" in str(error)
    else:
        raise AssertionError("configuration drift must require rebuild")

    report = changed_service.sync_documents(rebuild=True)
    assert store.reset_count == resets_before_rebuild + 1
    assert report.indexed_documents == 1


def test_search_filters_scores_and_preserves_citations(tmp_path):
    store = FakeVectorStore()
    rag = service(tmp_path, store)
    store.search_results = [
        (Document(page_content="可信证据", metadata={
            "chunk_id": "good", "source": "yuelu.txt", "page": 0,
            "section": "房源 1", "source_url": "https://example.test/good",
            "document_id": "doc-good",
        }), 0.82),
        (Document(page_content="弱相关", metadata={"chunk_id": "weak", "source": "other.txt"}), 0.2),
    ]

    chunks = rag.search("岳麓区租房")

    assert [chunk.chunk_id for chunk in chunks] == ["good"]
    assert chunks[0].page == 1
    assert chunks[0].source_url == "https://example.test/good"


def test_retrieval_service_applies_context_budget_and_refusal():
    class SearchStub:
        def __init__(self, chunks):
            self.chunks = chunks

        def search(self, query):
            return self.chunks

    chunks = [
        RetrievedChunk(str(index), "x" * 300, 0.9, f"source-{index}.txt")
        for index in range(3)
    ]
    service_with_results = RagRetrievalService(SearchStub(chunks), config={"max_context_chars": 500})
    empty_service = RagRetrievalService(SearchStub([]), config={"max_context_chars": 500})

    result = service_with_results.retrieve("  查询  ")
    empty = empty_service.retrieve("没有证据的问题")

    assert result.grounded is True
    assert result.query == "查询"
    assert sum(len(chunk.content) for chunk in result.chunks) == 500
    assert empty.grounded is False and empty.chunks == []

    tiny_budget = RagRetrievalService(SearchStub(chunks), config={"max_context_chars": 25}).retrieve("查询")
    assert sum(len(chunk.content) for chunk in tiny_budget.chunks) == 25


def test_agent_tool_payload_is_structured_and_safe(monkeypatch):
    from app.services import react_tools

    result = type("Result", (), {"to_dict": lambda self: {
        "query": "测试", "grounded": True,
        "chunks": [{"chunk_id": "c1", "content": "证据", "score": 0.9, "source": "source.txt"}],
    }})()
    fake_service = type("Service", (), {"retrieve": lambda self, query, **kwargs: result})()
    monkeypatch.setattr(react_tools, "_rag_service", lambda: fake_service)

    payload = json.loads(react_tools._rental_knowledge_payload(" 测试 "))

    assert payload["grounded"] is True
    assert payload["chunks"][0]["source"] == "source.txt"


def test_final_answer_enforces_grounding_and_citation_bounds(monkeypatch):
    monkeypatch.setattr("app.services.react_agent.review_grounded_answer", lambda *_args: False)
    from langchain_core.messages import AIMessage, ToolMessage
    from app.services.react_agent import _final_answer

    no_evidence = ToolMessage(
        content=json.dumps({"grounded": False, "chunks": []}),
        tool_call_id="call-1", name="search_rental_guidance",
    )
    evidence = ToolMessage(
        content=json.dumps({
            "grounded": True,
            "chunks": [{"source": "source.txt", "content": "月租为1800元"}],
        }),
        tool_call_id="call-2", name="search_rental_guidance",
    )

    assert "不足以确认" in _final_answer([no_evidence, AIMessage(content="我猜是1800元")])
    assert "先把能确认的依据" in _final_answer([evidence, AIMessage(content="答案见[2]")])
    assert _final_answer([evidence, AIMessage(content="月租为1800元[1]")]) == "月租为1800元[1]"
    assert "还没能对应清楚" in _final_answer([evidence, evidence, AIMessage(content="月租为1800元[1]")])


def test_empty_source_directory_fails_closed(tmp_path):
    store = FakeVectorStore()
    rag = service(tmp_path, store)
    try:
        rag.sync_documents(rebuild=True)
    except RuntimeError as error:
        assert "refusing destructive sync" in str(error)
    else:
        raise AssertionError("empty source directory must fail closed")
    assert store.reset_count == 0


def test_streaming_path_validates_tool_evidence(monkeypatch):
    from langchain_core.messages import AIMessage, ToolMessage
    from app.services import react_agent
    from app.services.query_router import QueryRoute

    class FakeAgent:
        def stream(self, *args, **kwargs):
            yield {"model": {"messages": [AIMessage(content="", tool_calls=[{
                "name": "search_rental_guidance", "args": {"query": "x"}, "id": "call-1"
            }])]}}
            yield {"tools": {"messages": [ToolMessage(
                content=json.dumps({"query": "x", "grounded": False, "chunks": []}),
                tool_call_id="call-1", name="search_rental_guidance",
            )]}}
            yield {"model": {"messages": [AIMessage(content="我猜答案是1800元")]}}

    monkeypatch.setattr(react_agent, "get_react_agent", lambda *_args, **_kwargs: FakeAgent())
    monkeypatch.setattr(
        react_agent, "_route_for_messages", lambda _messages: QueryRoute.RAG
    )
    events = list(react_agent.stream_react_agent([{"role": "user", "content": "x"}]))
    assert "不足以确认" in events[-1]["content"]


def test_interrupted_rebuild_blocks_search_and_can_recover(tmp_path):
    store = FakeVectorStore()
    rag = service(tmp_path, store)
    (rag.data_path / "source.txt").write_text("可靠房源资料", encoding="utf-8")
    rag.sync_documents()
    original_reset = store.reset_collection
    store.reset_collection = lambda: (_ for _ in ()).throw(RuntimeError("reset failed"))

    try:
        rag.sync_documents(rebuild=True)
    except RuntimeError as error:
        assert "reset failed" in str(error)
    else:
        raise AssertionError("simulated rebuild must fail")
    try:
        rag.search("房源")
    except RuntimeError as error:
        assert "incomplete rebuild" in str(error)
    else:
        raise AssertionError("search must reject an incomplete rebuild")

    store.reset_collection = original_reset
    assert rag.sync_documents(rebuild=True).indexed_documents == 1
    assert rag.search("房源") == []


def test_interrupted_incremental_update_fails_closed_and_auto_recovers(tmp_path):
    store = FakeVectorStore()
    rag = service(tmp_path, store)
    source = rag.data_path / "source.txt"
    source.write_text("第一版可靠资料", encoding="utf-8")
    rag.sync_documents()
    resets_before_failure = store.reset_count
    first_generation = json.loads(rag.manifest_path.read_text(encoding="utf-8"))["generation"]
    source.write_text("第二版可靠资料", encoding="utf-8")
    original_add = store.add_documents
    store.add_documents = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("add failed"))

    with pytest.raises(RuntimeError, match="add failed"):
        rag.sync_documents()
    assert json.loads(rag.manifest_path.read_text(encoding="utf-8"))["state"] == "updating"
    with pytest.raises(RuntimeError, match="incomplete"):
        rag.search("资料")

    store.add_documents = original_add
    report = rag.sync_documents()
    recovered = json.loads(rag.manifest_path.read_text(encoding="utf-8"))
    assert report.indexed_documents == 1
    assert store.reset_count == resets_before_failure + 1
    assert recovered["state"] == "ready"
    assert recovered["generation"] == first_generation + 1


def test_search_rejects_generation_change_during_query(tmp_path):
    store = FakeVectorStore()
    rag = service(tmp_path, store)
    (rag.data_path / "source.txt").write_text("可靠资料", encoding="utf-8")
    rag.sync_documents()

    def mutate_generation(query, k, **kwargs):
        manifest = json.loads(rag.manifest_path.read_text(encoding="utf-8"))
        manifest["generation"] += 1
        rag._write_manifest(manifest)
        return []

    store.similarity_search_with_relevance_scores = mutate_generation
    with pytest.raises(RuntimeError, match="changed during search"):
        rag.search("资料")


def test_ranking_and_answer_contract_metrics_are_deterministic():
    assert reciprocal_rank(["a", "b", "c"], ["b"]) == 0.5
    assert recall_at_k(["a", "b", "c"], ["b", "c"], 2) == 0.5
    metrics = evaluate_answer_contract(
        "押金按合同约定退还[1]",
        ["合同应明确押金金额及退还条件"],
        required_facts=[{
            "answer_terms": ["押金", "退还"],
            "evidence_terms": ["押金", "退还条件"],
        }],
    )
    assert metrics == {
        "citation_validity": 1.0,
        "citation_faithfulness": 1.0,
        "fact_consistency": 1.0,
    }


def test_index_file_lock_rejects_concurrent_writer(tmp_path):
    rag = service(tmp_path, FakeVectorStore())
    (rag.data_path / "source.txt").write_text("房源资料", encoding="utf-8")
    lock = FileLock(str(rag.manifest_path) + ".lock")
    with lock:
        try:
            rag.sync_documents()
        except Timeout:
            pass
        else:
            raise AssertionError("concurrent index writer must be rejected")


def test_evaluation_cli_fails_release_gate(monkeypatch, tmp_path):
    from core.rag import evaluate as evaluation

    monkeypatch.setattr(evaluation, "evaluate", lambda path: {
        "source_recall_at_k": 0.5, "refusal_accuracy": 1.0,
    })
    monkeypatch.setattr(sys, "argv", ["evaluate", "--dataset", str(tmp_path / "eval.json")])
    assert evaluation.main() == 1


def test_chat_model_factory_uses_deepseek_without_dashscope_key(monkeypatch):
    from langchain_openai import ChatOpenAI
    from app.core.config import settings
    from core.agent_model.factor import get_chat_model

    get_chat_model.cache_clear()
    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setattr(settings, "AI_CHAT_MODEL", "deepseek-v4-flash")
    monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "")

    model = get_chat_model()
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "deepseek-v4-flash"
    assert str(model.openai_api_base).rstrip("/") == "https://api.deepseek.com"
    get_chat_model.cache_clear()


def test_embedding_factory_uses_qwen37_model(monkeypatch):
    from app.core.config import settings
    from core.agent_model.factor import get_embedding_model

    get_embedding_model.cache_clear()
    monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "test-dashscope-key")
    monkeypatch.setattr(settings, "AI_EMBEDDING_MODEL", "qwen3.7-text-embedding")

    embedding = get_embedding_model()
    assert embedding.model == "qwen3.7-text-embedding"
    get_embedding_model.cache_clear()


def test_deepseek_errors_are_sanitized():
    from app.services.react_agent import _agent_error_message

    AuthenticationError = type("AuthenticationError", (Exception,), {})
    RateLimitError = type("RateLimitError", (Exception,), {})
    APIConnectionError = type("APIConnectionError", (Exception,), {})

    assert "DEEPSEEK_API_KEY" in _agent_error_message(AuthenticationError("private"))
    assert "过于频繁" in _agent_error_message(RateLimitError("private"))
    assert "无法连接 DeepSeek" in _agent_error_message(APIConnectionError("private"))


def test_streaming_agent_exposes_safe_deepseek_message(monkeypatch):
    from app.services import react_agent

    AuthenticationError = type("AuthenticationError", (Exception,), {})

    class FailedAgent:
        def stream(self, *args, **kwargs):
            raise AuthenticationError("private provider detail")

    monkeypatch.setattr(react_agent, "get_react_agent", lambda *_args, **_kwargs: FailedAgent())
    try:
        list(react_agent.stream_react_agent([{"role": "user", "content": "你好"}]))
    except RuntimeError as error:
        assert "DEEPSEEK_API_KEY" in str(error)
        assert "private provider detail" not in str(error)
    else:
        raise AssertionError("provider failures must stop the stream with a safe message")
