import json
from types import SimpleNamespace
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, ToolMessage
import pytest
import requests

from app.services.agent_errors import AgentPublicError
from app.services.query_constraints import (
    extract_house_constraints,
    merge_house_constraints,
    resolve_house_reference,
)
from app.services.query_router import QueryRoute, route_query
from app.services import react_agent, react_tools


@pytest.fixture(autouse=True)
def offline_answer_review(monkeypatch):
    """Keep deterministic grounding regressions independent of model services."""
    monkeypatch.setattr(react_agent, "review_grounded_answer", lambda *_args: False)


def _tool_message(name: str, payload: dict, call_id: str = "call-1") -> ToolMessage:
    return ToolMessage(
        name=name,
        tool_call_id=call_id,
        content=json.dumps(payload, ensure_ascii=False),
    )


def _house(**overrides):
    values = {
        "id": 1,
        "title": "整租·麓谷花园 2室1厅 南",
        "region": "岳麓",
        "block": "麓谷",
        "community": "麓谷花园",
        "area": 70,
        "direction": "南",
        "rooms": "2室1厅1卫",
        "price": 1900,
        "rent_type": "整租",
        "decoration": "精装",
        "subway": 1,
        "available": 1,
        "tag_new": 1,
        "image_url": None,
        "publish_time": None,
        "page_views": 10,
        "house_num": "H-1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_constraints_parse_chinese_budget_and_merge_latest_clear():
    parsed = extract_house_constraints("岳麓区，两千以内，两室整租，近地铁")
    assert parsed.region == "岳麓"
    assert parsed.max_price == 2000 and parsed.min_price is None
    assert parsed.room_count == 2 and parsed.rent_type == "整租"
    assert parsed.subway is True

    merged = merge_house_constraints([
        {"role": "user", "content": "岳麓区预算3000元整租"},
        {"role": "assistant", "content": "好的"},
        {"role": "user", "content": "改成芙蓉区，预算不限"},
    ])
    assert merged.region == "芙蓉"
    assert merged.min_price is None and merged.max_price is None
    assert merged.rent_type == "整租"


def test_reference_resolution_is_deterministic_and_ambiguous_when_needed():
    messages = [
        {"role": "assistant", "content": "- A｜房源ID 11\n- B｜房源ID 22"},
        {"role": "user", "content": "第二套呢"},
    ]
    assert resolve_house_reference(messages).house_id == 22
    messages[-1]["content"] = "这套呢"
    assert resolve_house_reference(messages).ambiguous is True

    unique = [
        {"role": "assistant", "content": "- A｜房源ID 11"},
        {"role": "user", "content": "那套多少钱？"},
    ]
    assert resolve_house_reference(unique).house_id == 11


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("岳麓区，两千以内", QueryRoute.SQL),
        ("房东不修空调怎么办", QueryRoute.RAG),
        ("押一付三是什么意思", QueryRoute.RAG),
        ("历史租房补贴政策有什么变化？", QueryRoute.RAG),
        ("当前房源和历史快照有什么区别？", QueryRoute.MIXED),
    ],
)
def test_router_covers_spoken_queries(query, expected):
    assert route_query(query) is expected


def test_router_inherits_expanded_anaphora():
    assert route_query("这套呢", ["推荐岳麓区房源"]) is QueryRoute.SQL
    assert route_query("第二套呢", ["推荐岳麓区房源"]) is QueryRoute.SQL
    assert route_query("那套多少钱", ["推荐岳麓区房源"]) is QueryRoute.SQL
    assert route_query("第二套有地铁吗", ["推荐岳麓区房源"]) is QueryRoute.SQL


def test_house_conflicts_and_unknown_blocks_are_pending():
    dirty = react_tools._house_payload(_house(
        id=48,
        title="合租·盘锦小区 2室1厅 南",
        region="岳麓",
        block="德政园",
        community="盘锦小区",
        rent_type="整租",
    ))
    assert dirty["verification_status"] == "pending_verification"
    assert set(dirty["verification_issues"]) == {
        "title_rent_type_conflict",
        "region_block_conflict",
    }

    unknown = react_tools._house_payload(_house(block="未收录商圈"))
    assert unknown["verification_status"] == "pending_verification"
    assert "block_region_unverified" in unknown["verification_issues"]


def test_sql_tool_returns_normalized_applied_filters_and_counts(monkeypatch):
    query = MagicMock()
    query.filter.return_value = query
    query.count.return_value = 1
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = [_house()]
    db = MagicMock()
    db.query.return_value = query
    context = MagicMock()
    context.__enter__.return_value = db
    context.__exit__.return_value = False
    monkeypatch.setattr(react_tools, "SessionLocal", MagicMock(return_value=context))

    payload = json.loads(react_tools.search_houses_by_criteria.invoke({
        "region": "岳麓区", "max_price": 2000, "rooms": "2室", "rent_type": "整租",
    }))

    assert payload["tool_kind"] == "criteria_search"
    assert payload["applied_filters"]["region"] == "岳麓"
    assert payload["applied_filters"]["max_price"] == 2000
    assert payload["verified_count"] == 1


def test_sql_final_guard_rejects_wrong_tool_filters_and_rows():
    context = react_agent._query_context([
        {"role": "user", "content": "推荐岳麓区2000元以内的整租"}
    ])
    wrong_filters = _tool_message("search_houses_by_criteria", {
        "tool_kind": "criteria_search",
        "applied_filters": {
            "region": "天心", "min_price": None, "max_price": 9000,
            "min_area": None, "max_area": None, "rooms": None,
            "rent_type": "整租", "subway": None, "decoration": None,
        },
        "houses": [react_tools._house_payload(_house(region="天心", price=9000))],
    })
    answer = react_agent._final_answer(
        [wrong_filters, AIMessage(content="模型说符合")], QueryRoute.SQL, context
    )
    assert "没有完整保留你的要求" in answer
    assert "麓谷花园" not in answer

    correct_filters = {
        "region": "岳麓", "min_price": None, "max_price": 2000,
        "min_area": None, "max_area": None, "rooms": None,
        "rent_type": "整租", "subway": None, "decoration": None,
    }
    wrong_row = _tool_message("search_houses_by_criteria", {
        "tool_kind": "criteria_search", "applied_filters": correct_filters,
        "houses": [react_tools._house_payload(_house(price=2500))],
    })
    answer = react_agent._final_answer(
        [wrong_row, AIMessage(content="模型说符合")], QueryRoute.SQL, context
    )
    assert "没有满足这次的筛选条件" in answer


def test_conflicting_house_uses_user_friendly_safety_message():
    context = react_agent._query_context([
        {"role": "user", "content": "推荐岳麓区2000元以内的整租"}
    ])
    dirty = react_tools._house_payload(_house(
        id=48, title="合租·盘锦小区 2室1厅 南", region="岳麓",
        block="德政园", community="盘锦小区", price=2000,
    ))
    payload = _tool_message("search_houses_by_criteria", {
        "tool_kind": "criteria_search",
        "applied_filters": {
            "region": "岳麓", "min_price": None, "max_price": 2000,
            "min_area": None, "max_area": None, "rooms": None,
            "rent_type": "整租", "subway": None, "decoration": None,
        },
        "total_count": 1, "houses": [dirty],
    })
    answer = react_agent._final_answer(
        [payload, AIMessage(content="强烈推荐")], QueryRoute.SQL, context
    )
    assert "信息完整" in answer
    assert "避免你白跑一趟" in answer
    assert "盘锦小区" not in answer and "房源ID 48" not in answer
    assert "实时数据库" not in answer
    assert "待核验候选" not in answer
    assert "字段存在冲突" not in answer
    assert "强烈推荐" not in answer


def test_verified_search_uses_natural_recommendation_copy():
    context = react_agent._query_context([
        {"role": "user", "content": "推荐岳麓区2000元以内的整租"}
    ])
    house = react_tools._house_payload(_house(id=8, title="麓谷花园", price=1800))
    payload = _tool_message("search_houses_by_criteria", {
        "tool_kind": "criteria_search",
        "applied_filters": {
            "region": "岳麓", "min_price": None, "max_price": 2000,
            "min_area": None, "max_area": None, "rooms": None,
            "rent_type": "整租", "subway": None, "decoration": None,
        },
        "total_count": 1, "houses": [house],
    })
    answer = react_agent._final_answer(
        [payload, AIMessage(content="强烈推荐")], QueryRoute.SQL, context
    )
    assert answer.startswith("可以，先看看这套")
    assert "麓谷花园" in answer and "房源编号：8" in answer
    assert "实时数据库" not in answer


def test_rag_route_requires_correct_tool_and_fact_level_support():
    context = react_agent._query_context([
        {"role": "user", "content": "押金退还要写进合同吗"}
    ])
    assert "没有查到可以核对" in react_agent._final_answer(
        [AIMessage(content="凭记忆回答")], QueryRoute.RAG, context
    )

    evidence = _tool_message("search_rental_guidance", {
        "query": "押金退还要写进合同吗",
        "grounded": True,
        "chunks": [{"content": "签订租赁合同时，应明确写明押金金额和退还条件。", "source": "guide.txt"}],
    })
    valid = react_agent._final_answer(
        [evidence, AIMessage(content="签订租赁合同时，应明确写明押金金额和退还条件[1]。")],
        QueryRoute.RAG,
        context,
    )
    assert valid == "签订租赁合同时，应明确写明押金金额和退还条件[1]。"

    with_heading = react_agent._final_answer(
        [evidence, AIMessage(content="### 押金退还建议\n签订租赁合同时，应明确写明押金金额和退还条件[1]。")],
        QueryRoute.RAG,
        context,
    )
    assert with_heading.startswith("### 押金退还建议")

    unsupported = react_agent._final_answer(
        [evidence, AIMessage(content="法律规定押金不得超过十万元[1]。")],
        QueryRoute.RAG,
        context,
    )
    assert "先把能确认的依据" in unsupported
    assert "十万元" not in unsupported

    for contradiction in (
        "合同约定房东可以随意没收押金[1]。",
        "租赁合同中房东可以永久扣留押金[1]。",
        "合同写明后房东便可以随意没收押金[1]。",
        "合同押金归房东[1]。",
        "合同押金不用退[1]。",
    ):
        rejected = react_agent._final_answer(
            [evidence, AIMessage(content=contradiction)], QueryRoute.RAG, context
        )
        assert "先把能确认的依据" in rejected
        assert contradiction not in rejected

    wrong_query = _tool_message("search_rental_guidance", {
        "query": "另一个问题",
        "grounded": True,
        "chunks": [{"content": "签订租赁合同时，应明确写明押金金额和退还条件。"}],
    })
    assert "没有准确对应" in react_agent._final_answer(
        [wrong_query, AIMessage(content="签订租赁合同时，应明确写明押金金额和退还条件[1]。")],
        QueryRoute.RAG,
        context,
    )


def test_rag_service_failure_is_not_reported_as_zero_hits(monkeypatch):
    failure_type = type("DashScopeEmbeddingError", (RuntimeError,), {})
    failure = failure_type("private key=secret")
    failure.retryable = True
    failure.status_code = 429
    monkeypatch.setattr(
        react_tools,
        "_rag_service",
        lambda: SimpleNamespace(retrieve=lambda *_args, **_kwargs: (_ for _ in ()).throw(failure)),
    )

    with pytest.raises(AgentPublicError) as exc_info:
        react_tools._rental_knowledge_payload("押金怎么退")
    assert exc_info.value.code == "RAG_UNAVAILABLE"
    assert exc_info.value.retryable is True
    assert "secret" not in str(exc_info.value)


def test_weather_http_error_log_does_not_include_api_key(monkeypatch, caplog):
    secret = "TOPSECRET-WEATHER-KEY"
    monkeypatch.setattr(react_tools.settings, "GAODE_WEATHER_KEY", secret)

    class FailedResponse:
        status_code = 500

        def raise_for_status(self):
            response = requests.Response()
            response.status_code = 500
            response.url = f"https://example.test/weather?key={secret}"
            raise requests.HTTPError("provider failed", response=response)

    monkeypatch.setattr(react_tools.requests, "get", lambda *_args, **_kwargs: FailedResponse())
    payload = json.loads(react_tools.get_weather_for_visit.invoke({"city": "长沙"}))

    assert payload["error"]
    assert secret not in caplog.text
