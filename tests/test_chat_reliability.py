from datetime import timedelta
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.api.v1 import chat_ai
from app.core.time import utc_now_naive
from app.models.house import HouseInfo
from app.services.agent_errors import AgentPublicError
from app.services.query_router import QueryRoute
from app.services import react_agent, react_tools


def test_route_tool_whitelists_keep_live_inventory_out_of_rag():
    names = {
        route: {tool.name for tool in tools}
        for route, tools in react_agent._TOOLS_BY_ROUTE.items()
    }
    assert "search_houses_by_criteria" in names[QueryRoute.SQL]
    assert "search_houses_by_criteria" not in names[QueryRoute.RAG]
    assert names[QueryRoute.RAG] == {"search_rental_guidance"}
    assert names[QueryRoute.HISTORICAL_SNAPSHOT] == {"search_historical_snapshots"}


def test_routed_agent_factory_returns_created_agent(monkeypatch):
    sentinel = object()
    create_agent = MagicMock(return_value=sentinel)
    monkeypatch.setattr("langchain.agents.create_agent", create_agent)
    monkeypatch.setattr("core.agent_model.factor.get_chat_model", lambda: object())
    monkeypatch.setattr("core.agent_utils.prompt_loader.load_system_prompt", lambda: "system")
    react_agent.get_react_agent.cache_clear()

    result = react_agent.get_react_agent(QueryRoute.RAG.value)

    assert result is sentinel
    assert [tool.name for tool in create_agent.call_args.kwargs["tools"]] == [
        "search_rental_guidance"
    ]
    react_agent.get_react_agent.cache_clear()


def test_agent_error_keeps_retry_metadata_without_private_payload():
    RateLimitError = type("RateLimitError", (Exception,), {})
    message, code, retryable, retry_after = react_agent._deepseek_error_details(
        RateLimitError("private provider response")
    )
    assert "private provider response" not in message
    assert (code, retryable, retry_after) == ("RATE_LIMITED", True, 2)


def test_public_error_replaces_accidentally_embedded_secret():
    error = AgentPublicError(
        "provider failed: https://example.test?key=TOPSECRET",
        code="RAG_UNAVAILABLE",
        provider="dashscope",
        retryable=True,
        retry_after=3,
    )

    assert "TOPSECRET" not in str(error)
    assert error.code == "RAG_UNAVAILABLE"
    assert error.provider == "dashscope"
    assert error.retryable is True
    assert error.retry_after == 3


def test_sse_error_preserves_public_metadata_and_actual_retry_state(monkeypatch):
    def fail(_history):
        raise AgentPublicError(
            "DeepSeek 请求过于频繁，请稍后重试。",
            code="RATE_LIMITED",
            provider="deepseek",
            retryable=True,
            retry_after=7,
        )
        yield  # pragma: no cover - keeps this a generator

    monkeypatch.setattr(react_agent, "stream_react_agent", fail)
    monkeypatch.setattr(chat_ai, "_run_cancelled", lambda *_args: False)
    monkeypatch.setattr(chat_ai, "_run_can_retry", lambda *_args: True)
    set_state = MagicMock(return_value=True)
    monkeypatch.setattr(chat_ai, "_set_run_state", set_state)

    events = list(chat_ai._stream_events(
        42,
        [{"role": "user", "content": "你好"}],
        "12345678-1234-5678-1234-567812345678",
        lease_token="lease-1",
    ))
    payload = json.loads(events[-1][6:])

    assert payload == {
        "type": "error",
        "code": "RATE_LIMITED",
        "message": "DeepSeek 请求过于频繁，请稍后重试。",
        "provider": "deepseek",
        "retryable": True,
        "retry_after": 7,
        "request_id": "12345678-1234-5678-1234-567812345678",
        "session_id": 42,
        "run_status": "retry_wait",
    }
    assert set_state.call_args.args[:2] == (
        "12345678-1234-5678-1234-567812345678",
        "retry_wait",
    )
    assert set_state.call_args.kwargs["error_code"] == "RATE_LIMITED"


def test_sse_error_never_claims_retry_when_state_update_lost_race(monkeypatch):
    def fail(_history):
        raise AgentPublicError(
            "知识库暂时不可用，请稍后重试。",
            code="RAG_UNAVAILABLE",
            provider="rag",
            retryable=True,
            retry_after=2,
        )
        yield  # pragma: no cover - keeps this a generator

    monkeypatch.setattr(react_agent, "stream_react_agent", fail)
    monkeypatch.setattr(chat_ai, "_run_cancelled", lambda *_args: False)
    monkeypatch.setattr(chat_ai, "_run_can_retry", lambda *_args: True)
    monkeypatch.setattr(chat_ai, "_set_run_state", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(
        chat_ai, "_current_run_recovery_state", lambda _request_id: ("failed", None)
    )

    events = list(chat_ai._stream_events(
        42,
        [{"role": "user", "content": "押金怎么退"}],
        "12345678-1234-5678-1234-567812345679",
        lease_token="lease-2",
    ))
    payload = json.loads(events[-1][6:])

    assert payload["code"] == "RAG_UNAVAILABLE"
    assert payload["run_status"] == "failed"
    assert payload["retryable"] is False
    assert payload["retry_after"] is None


def test_sse_error_after_streamed_text_is_terminal(monkeypatch):
    def fail_after_text(_history):
        yield {"type": "token", "content": "公开正文" * 20}
        raise AgentPublicError(
            "DeepSeek 请求过于频繁，请稍后重试。",
            code="RATE_LIMITED",
            provider="deepseek",
            retryable=True,
            retry_after=2,
        )

    monkeypatch.setattr(react_agent, "stream_react_agent", fail_after_text)
    monkeypatch.setattr(chat_ai, "_touch_lease", lambda *_args: True)
    monkeypatch.setattr(chat_ai, "_run_cancelled", lambda *_args: False)
    can_retry = MagicMock(return_value=True)
    monkeypatch.setattr(chat_ai, "_run_can_retry", can_retry)
    set_state = MagicMock(return_value=True)
    monkeypatch.setattr(chat_ai, "_set_run_state", set_state)

    events = list(chat_ai._stream_events(
        42,
        [{"role": "user", "content": "你好"}],
        "12345678-1234-5678-1234-567812345680",
        lease_token="lease-3",
    ))
    payload = json.loads(events[-1][6:])

    assert any('"type": "chunk"' in event for event in events[:-1])
    assert payload["run_status"] == "failed"
    assert payload["retryable"] is False
    assert payload["retry_after"] is None
    can_retry.assert_not_called()
    assert set_state.call_args.args[1] == "failed"


def test_agent_http_exception_has_machine_readable_retry_contract():
    error = chat_ai._agent_http_exception(
        429,
        "AGENT_BUSY",
        request_id="12345678-1234-5678-1234-567812345678",
        retryable=True,
        retry_after=2,
        run_status="retry_wait",
    )

    assert error.status_code == 429
    assert error.headers == {"Retry-After": "2"}
    assert error.detail == {
        "code": "AGENT_BUSY",
        "message": "AI 请求繁忙，请稍后重试。",
        "provider": None,
        "retryable": True,
        "retry_after": 2,
        "type": "error",
        "request_id": "12345678-1234-5678-1234-567812345678",
        "run_status": "retry_wait",
    }


def test_sql_route_requires_tool_and_renders_only_tool_fields(monkeypatch):
    monkeypatch.setattr(react_agent, "review_grounded_answer", lambda *_args: False)
    import json
    from langchain_core.messages import AIMessage, ToolMessage

    no_tool = react_agent._final_answer(
        [AIMessage(content="我记得有一套虚构房源")], QueryRoute.SQL
    )
    assert "未取得实时数据库结果" in no_tool
    evidence = ToolMessage(
        name="search_houses_by_criteria",
        tool_call_id="sql-1",
        content=json.dumps({
            "total_count": 1,
            "returned_count": 1,
            "has_more": False,
            "houses": [{
                "id": 48, "title": "盘锦小区", "region": "岳麓", "block": "麓谷",
                "price": 2000, "area": 83, "rooms": "2室1厅1卫", "rent_type": "整租",
                "verification_status": "verified",
            }],
        }, ensure_ascii=False),
    )
    answer = react_agent._final_answer(
        [evidence, AIMessage(content="虚构：只剩这一套，而且近地铁")], QueryRoute.SQL
    )
    assert "盘锦小区" in answer and "房源编号：48" in answer
    assert "近地铁" not in answer and "只剩" not in answer


def test_history_is_bounded_and_keeps_chronological_order():
    records = [
        SimpleNamespace(id=value, role="user", content=f"message-{value}")
        for value in range(40, 10, -1)
    ]
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = records
    db = MagicMock()
    db.query.return_value = query

    history = chat_ai._history(db, 7)

    assert len(history) == 30
    assert history[0]["content"] == "message-11"
    assert history[-1]["content"] == "message-40"


def test_generator_close_marks_retry_wait_and_releases_admission(monkeypatch):
    touch_lease = MagicMock(return_value=True)
    monkeypatch.setattr(chat_ai, "_touch_lease", touch_lease)
    monkeypatch.setattr(chat_ai, "_run_cancelled", lambda *_args: False)
    monkeypatch.setattr(chat_ai, "_run_can_retry", lambda *_args: True)
    set_state = MagicMock()
    monkeypatch.setattr(chat_ai, "_set_run_state", set_state)
    monkeypatch.setattr(
        react_agent,
        "stream_react_agent",
        lambda _history: iter([{"type": "status", "status": "查询中"}]),
    )
    admission = MagicMock()
    generator = chat_ai._stream_events(
        9,
        [{"role": "user", "content": "查询"}],
        "request-1",
        lease_token="lease-1",
        admission=admission,
    )
    next(generator)
    next(generator)
    next(generator)
    generator.close()

    set_state.assert_called_once()
    assert set_state.call_args.args[:2] == ("request-1", "retry_wait")
    assert set_state.call_args.kwargs["error_code"] == "CLIENT_DISCONNECTED"
    touch_lease.assert_called_once()
    admission.release.assert_called_once()


def test_generator_close_after_public_chunk_is_not_retried(monkeypatch):
    monkeypatch.setattr(chat_ai, "_touch_lease", lambda *_args: True)
    monkeypatch.setattr(chat_ai, "_run_cancelled", lambda *_args: False)
    monkeypatch.setattr(chat_ai, "_run_can_retry", lambda *_args: True)
    set_state = MagicMock()
    monkeypatch.setattr(chat_ai, "_set_run_state", set_state)
    monkeypatch.setattr(
        react_agent,
        "stream_react_agent",
        lambda _history: iter([{"type": "token", "content": "公开正文" * 20}]),
    )
    admission = MagicMock()
    generator = chat_ai._stream_events(
        9,
        [{"role": "user", "content": "你好"}],
        "request-streamed",
        lease_token="lease-streamed",
        admission=admission,
    )
    next(generator)
    next(generator)
    chunk_event = next(generator)
    assert '"type": "chunk"' in chunk_event
    generator.close()

    assert set_state.call_args.args[:2] == ("request-streamed", "failed")
    assert set_state.call_args.kwargs["next_retry_at"] is None
    admission.release.assert_called_once()


def test_stale_run_recovery_distinguishes_retry_and_cancel():
    now = utc_now_naive()
    retry = SimpleNamespace(
        cancel_requested=False, status="running", error_code=None,
        lease_token="a", lease_expires_at=now - timedelta(seconds=1),
        heartbeat_at=None, next_retry_at=None, finished_at=None, updated_at=None,
    )
    cancel = SimpleNamespace(
        cancel_requested=True, status="running", error_code=None,
        lease_token="b", lease_expires_at=now - timedelta(seconds=1),
        heartbeat_at=None, next_retry_at=None, finished_at=None, updated_at=None,
    )
    query = MagicMock()
    query.filter.return_value = query
    query.update.side_effect = [1, 1, 0]
    db = MagicMock()
    db.query.return_value = query

    assert chat_ai.recover_stale_agent_runs(db, now=now) == 2
    assert query.update.call_count == 3
    db.commit.assert_called_once()


def test_get_run_recovers_stale_work_and_returns_resume_metadata(monkeypatch):
    request_id = "12345678-1234-5678-1234-567812345678"
    next_retry_at = utc_now_naive() + timedelta(seconds=3)
    heartbeat_at = utc_now_naive() - timedelta(seconds=10)
    run = SimpleNamespace(
        request_id=request_id,
        user_id=7,
        session_id=21,
        user_message_id=31,
        assistant_message_id=None,
        status="retry_wait",
        cancel_requested=False,
        attempt_count=1,
        error_code="PROCESS_INTERRUPTED",
        heartbeat_at=heartbeat_at,
        next_retry_at=next_retry_at,
        finished_at=None,
    )
    db = MagicMock()
    db.get.return_value = run
    recover = MagicMock(return_value=0)
    monkeypatch.setattr(chat_ai, "recover_stale_agent_runs", recover)

    response = chat_ai.get_agent_run(
        UUID(request_id),
        db=db,
        current_user=SimpleNamespace(id=7),
    )
    data = response.data

    recover.assert_called_once_with(db)
    assert data["request_id"] == request_id
    assert data["session_id"] == 21
    assert data["user_message_id"] == 31
    assert data["assistant_message_id"] is None
    assert data["retryable"] is True
    assert 0 <= data["retry_after"] <= 3
    assert data["error"]["code"] == "PROCESS_INTERRUPTED"
    assert data["error"]["retryable"] is True
    assert data["error"]["retry_after"] == data["retry_after"]
    assert data["heartbeat_at"] == heartbeat_at.isoformat()


def test_router_covers_ambiguous_live_and_dispute_phrasing():
    from app.services.query_router import route_query

    assert route_query("岳麓区均价") is QueryRoute.SQL
    assert route_query("岳麓区2000左右有吗") is QueryRoute.SQL
    assert route_query("房东不退钱怎么办") is QueryRoute.RAG


def test_feedback_sanitizer_removes_common_identifiers():
    value = chat_ai._sanitize_failure_text(
        "电话13800138000，身份证430102199001011234，邮箱a@example.com，Bearer abcdefghijklmnop"
    )
    assert "13800138000" not in value
    assert "430102199001011234" not in value
    assert "a@example.com" not in value
    assert "abcdefghijklmnop" not in value
    extended = chat_ai._sanitize_failure_text(
        "姓名：张三，地址：长沙市岳麓区某街道123号，银行卡6222021234567890，微信: wx_test88"
    )
    assert "张三" not in extended
    assert "某街道" not in extended
    assert "6222021234567890" not in extended
    assert "wx_test88" not in extended


def test_house_query_validation_and_schema_are_consistent():
    assert react_tools._normalized_region("长沙市岳麓区") == "岳麓"
    with pytest.raises(ValueError):
        react_tools._normalized_region("岳区")
    with pytest.raises(ValueError):
        react_tools._validate_range("价格", 3000, 2000)
    assert HouseInfo.__table__.c.house_num.type.length == 255

    root = Path(__file__).parents[1]
    migration = (root / "migrations/versions/007_rag_reliability.py").read_text(encoding="utf-8")
    sql = (root / "flaskhousesystem.sql").read_text(encoding="utf-8")
    for field in (
        "attempt_count", "heartbeat_at", "lease_token", "lease_expires_at",
        "next_retry_at", "finished_at", "rag_failure_case",
    ):
        assert field in migration
        assert field in sql


def test_general_route_stream_preserves_token_whitespace(monkeypatch):
    from langchain_core.messages import AIMessage, AIMessageChunk

    class FakeAgent:
        def stream(self, *_args, **_kwargs):
            yield (
                "messages",
                (AIMessageChunk(content="你好"), {"langgraph_node": "model"}),
            )
            yield (
                "messages",
                (AIMessageChunk(content=" 世界"), {"langgraph_node": "model"}),
            )
            yield (
                "updates",
                {"model": {"messages": [AIMessage(content="你好 世界")]}},
            )

    monkeypatch.setattr(
        react_agent, "_route_for_messages", lambda _messages: QueryRoute.GENERAL
    )
    monkeypatch.setattr(react_agent, "_get_agent_for_messages", lambda _messages: FakeAgent())

    events = list(react_agent.stream_react_agent([{"role": "user", "content": "你好"}]))

    assert not any(event["type"] == "token" for event in events)
    assert events[-1] == {"type": "answer", "content": "你好 世界"}


def test_validated_answer_chunking_is_lossless():
    answer = "第一段。第二段包含 Markdown **重点**，以及 emoji 🏠。"
    chunks = list(chat_ai._safe_text_chunks(answer, max_chars=8))

    assert len(chunks) > 1
    assert "".join(chunks) == answer
    assert all(len(chunk) <= 8 for chunk in chunks)


def test_validated_sse_chunks_equal_persisted_answer(monkeypatch):
    import json

    answer = "这是经过 SQL 或 RAG 校验后的较长答案。它应当分成多个事件，并与数据库内容完全一致。"
    stream_db = MagicMock()
    stream_db.get.return_value = SimpleNamespace(updated_at=None)
    context = MagicMock()
    context.__enter__.return_value = stream_db
    context.__exit__.return_value = False
    monkeypatch.setattr(chat_ai, "SessionLocal", MagicMock(return_value=context))
    monkeypatch.setattr(
        react_agent,
        "stream_react_agent",
        lambda _history: iter([{"type": "answer", "content": answer}]),
    )

    events = list(chat_ai._stream_events(42, [{"role": "user", "content": "查询"}]))
    payloads = [json.loads(event[6:]) for event in events if event.startswith("data: ")]
    chunks = [payload["content"] for payload in payloads if payload["type"] == "chunk"]
    saved_message = stream_db.add.call_args.args[0]

    assert len(chunks) > 1
    assert "".join(chunks) == saved_message.content == answer


def test_long_model_chunk_cannot_hide_private_protocol(monkeypatch):
    monkeypatch.setattr(
        react_agent,
        "stream_react_agent",
        lambda _history: iter([
            {"type": "token", "content": "Thought: private" + "公开内容" * 80},
        ]),
    )

    events = list(chat_ai._stream_events(42, [{"role": "user", "content": "你好"}]))

    assert any('"type": "error"' in event for event in events)
    assert not any('"type": "chunk"' in event for event in events)


# ---------------------------------------------------------------------------
# RAG-route true token streaming
# ---------------------------------------------------------------------------
from langchain_core.messages import AIMessage, AIMessageChunk


class _RagStreamFakeAgent:
    """Yields token-level messages plus update dicts like the real LangGraph agent."""

    def __init__(self, tokens):
        self._tokens = tokens

    def stream(self, *_args, **_kwargs):
        for token in self._tokens:
            yield ("messages", (AIMessageChunk(content=token), {"langgraph_node": "model"}))
        yield ("updates", {"model": {"messages": [AIMessage(content="".join(self._tokens))]}})


def _patch_rag_route(monkeypatch, fake_agent, final_answer):
    monkeypatch.setattr(
        react_agent, "_route_for_messages", lambda _messages: QueryRoute.RAG
    )
    monkeypatch.setattr(react_agent, "_get_agent_for_messages", lambda _messages: fake_agent)
    monkeypatch.setattr(react_agent, "_final_answer", lambda *_args, **_kwargs: final_answer)


def test_rag_route_streams_tokens_without_override(monkeypatch):
    from langchain_core.messages import AIMessage, AIMessageChunk

    tokens = ["知识库", "答案 [1]"]
    _patch_rag_route(monkeypatch, _RagStreamFakeAgent(tokens), "".join(tokens))

    events = list(react_agent.stream_react_agent([{"role": "user", "content": "怎么签合同？"}]))

    assert not any(event["type"] == "token" for event in events)
    assert events[-1] == {"type": "answer", "content": "".join(tokens)}
    assert not any(event["type"] == "answer_override" for event in events)


def test_rag_route_emits_override_when_validated_answer_differs(monkeypatch):
    from langchain_core.messages import AIMessage, AIMessageChunk

    _patch_rag_route(
        monkeypatch,
        _RagStreamFakeAgent(["未校验的模型原话"]),
        "校验 [1] 后的权威答案",
    )

    events = list(react_agent.stream_react_agent([{"role": "user", "content": "怎么签合同？"}]))

    override_index = [i for i, event in enumerate(events) if event["type"] == "answer_override"]
    assert not override_index
    assert not any(event["type"] == "token" for event in events)
    assert events[-1] == {"type": "answer", "content": "校验 [1] 后的权威答案"}


def test_stream_events_emits_replace_event_on_override(monkeypatch):
    answer = "校验 [1] 后的权威答案，比已流出内容更长，需要整体替换。"
    stream_db = MagicMock()
    stream_db.get.return_value = SimpleNamespace(updated_at=None)
    context = MagicMock()
    context.__enter__.return_value = stream_db
    context.__exit__.return_value = False
    monkeypatch.setattr(chat_ai, "SessionLocal", MagicMock(return_value=context))
    monkeypatch.setattr(
        react_agent,
        "stream_react_agent",
        lambda _history: iter([
            {"type": "token", "content": "未校验的模型原话" * 10},
            {"type": "answer_override", "content": answer},
            {"type": "answer", "content": answer},
        ]),
    )

    events = list(chat_ai._stream_events(42, [{"role": "user", "content": "知识库问题"}]))
    payloads = [json.loads(event[6:]) for event in events if event.startswith("data: ")]
    replaces = [payload for payload in payloads if payload["type"] == "replace"]
    chunks = [payload["content"] for payload in payloads if payload["type"] == "chunk"]
    saved_message = stream_db.add.call_args.args[0]

    assert len(replaces) == 1
    assert replaces[0]["content"] == saved_message.content == answer
    # The replace event carries the full text; no stale pre-validation chunk
    # may appear after it.
    assert "".join(chunks) != answer
    assert payloads[-1]["type"] == "done"
