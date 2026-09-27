"""Conversation-level contracts for helpful, evidence-bounded responses."""

import json

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from app.services import react_agent
from app.services.query_router import QueryRoute


def knowledge_message():
    """Supply a small, correctly bound deposit guidance result."""
    return ToolMessage(name="search_rental_guidance", tool_call_id="knowledge-1", content=json.dumps({
        "query": "押金退还要写进合同吗", "grounded": True,
        "chunks": [{"content": "合同应写明押金金额及退还条件。", "source": "guide.txt"}],
    }))


def test_faithful_paraphrase_is_not_replaced_by_template(monkeypatch):
    """Allow reviewed paraphrases without requiring verbatim evidence sentences."""
    monkeypatch.setattr(react_agent, "review_grounded_answer", lambda *_args: True)
    context = react_agent._query_context([{"role": "user", "content": "押金退还要写进合同吗"}])
    answer = "建议把押金金额和退还条件写清楚，避免之后各说各的。[1]"
    assert react_agent._final_answer([knowledge_message(), AIMessage(content=answer)], QueryRoute.RAG, context) == answer


def test_failed_review_returns_evidence_not_internal_error(monkeypatch):
    """Keep useful source material without repeating a rejected conclusion."""
    monkeypatch.setattr(react_agent, "review_grounded_answer", lambda *_args: False)
    context = react_agent._query_context([{"role": "user", "content": "押金退还要写进合同吗"}])
    answer = react_agent._final_answer([knowledge_message(), AIMessage(content="房东可以永远不退押金")], QueryRoute.RAG, context)
    assert "合同应写明押金金额及退还条件" in answer
    assert "永远不退" not in answer
    assert "校验" not in answer and "换一种问法" not in answer


def test_relative_budget_clarifies_without_calling_model(monkeypatch):
    """Ask one focused question before changing a user's price constraint."""
    def unexpected_model(_messages):
        """Fail if clarification unnecessarily calls a provider."""
        raise AssertionError("model must not run")
    monkeypatch.setattr(react_agent, "_get_agent_for_messages", unexpected_model)
    history = [{"role": "user", "content": "岳麓区1500元以内整租"}, {"role": "user", "content": "贵一点也行"}]
    answer = react_agent.invoke_react_agent(history)
    assert "租金最多" in answer
    assert list(react_agent.stream_react_agent(history)) == [{"type": "answer", "content": answer}]


def test_rag_stream_collects_tuple_updates_without_leaking_draft(monkeypatch):
    """Handle actual multi-mode graph updates before publishing checked content."""
    class FakeAgent:
        """Model stream containing an unsupported draft and real tool updates."""
        def stream(self, *_args, **_kwargs):
            """Emit the same tuple shape as the graph streaming API."""
            yield ("messages", (AIMessageChunk(content="押金归房东"), {"langgraph_node": "model"}))
            yield ("updates", {"tools": {"messages": [knowledge_message()]}})
            yield ("updates", {"model": {"messages": [AIMessage(content="合同应写明押金金额及退还条件[1]。")]}})
    monkeypatch.setattr(react_agent, "_get_agent_for_messages", lambda _: FakeAgent())
    events = list(react_agent.stream_react_agent([{"role": "user", "content": "押金退还要写进合同吗"}]))
    assert not any(event["type"] == "token" for event in events)
    assert events[-1]["content"] == "合同应写明押金金额及退还条件[1]。"


def test_no_match_copy_does_not_invent_location_or_budget():
    """Never suggest a hardcoded Yuelu region or an invented price adjustment."""
    answer = react_agent.format_search_answer([{"verification_status": "pending_verification"}], {})
    assert "岳麓" not in answer and "500" not in answer


def test_budget_reply_routes_back_to_search():
    """A bare amount answers the assistant's own focused clarification."""
    history = [{"role": "user", "content": "岳麓区1500以内整租"},
               {"role": "assistant", "content": "每月租金最多能接受多少元？"},
               {"role": "user", "content": "1800"}]
    context = react_agent._query_context(history)
    assert context.route is QueryRoute.SQL
    assert context.constraints.max_price == 1800


def test_approximate_budget_is_not_a_five_hundred_yuan_expansion():
    """Keep the disclosed approximate range proportional to the requested rent."""
    context = react_agent._query_context([{"role": "user", "content": "岳麓区1500元左右整租"}])
    assert context.constraints.min_price == 1350
    assert context.constraints.max_price == 1650


def test_mixed_answer_review_receives_both_fact_sources(monkeypatch):
    """Review listing facts against SQL, not exclusively against legal excerpts."""
    query = "推荐岳麓区房源并说明签约注意事项"
    context = react_agent._query_context([{"role": "user", "content": query}])
    listing = ToolMessage(name="search_houses_by_criteria", tool_call_id="house-1", content=json.dumps({
        "applied_filters": {"region": "岳麓"},
        "houses": [{"id": 50, "region": "岳麓", "price": 1000, "verification_status": "verified"}],
    }))
    knowledge = ToolMessage(name="search_rental_guidance", tool_call_id="knowledge-1", content=json.dumps({
        "query": query, "grounded": True, "chunks": [{"content": "合同应写明押金金额。"}],
    }))
    def review(_query, _answer, evidence):
        """Verify evidence-source composition without calling an external model."""
        assert evidence["kind"] == "mixed"
        assert evidence["houses"][0]["id"] == 50
        assert evidence["chunks"]
        return True
    monkeypatch.setattr(react_agent, "review_grounded_answer", review)
    answer = "房源编号：50，租金1000元/月。签约时记得写清押金金额[1]。"
    assert react_agent._final_answer([listing, knowledge, AIMessage(content=answer)], context.route, context) == answer


def test_filtered_popular_query_does_not_require_unfiltered_tool():
    """Do not issue a tool instruction that the SQL guard must later reject."""
    messages = [{"role": "user", "content": "岳麓区2000元以内热门房源"}]
    context = react_agent._query_context(messages)
    instruction = react_agent._messages_with_query_contract(messages, context)[-1]["content"]
    assert "必须调用 search_houses_by_criteria" in instruction
    assert "必须调用 get_popular_houses" not in instruction


def test_orientation_is_not_proof_of_cross_ventilation():
    """Block an unsupported benefit observed during the real-model smoke test."""
    from app.services.answer_review import review_grounded_answer
    assert not review_grounded_answer("推荐房源", "这套房南北通透", {
        "kind": "houses", "houses": [{"id": 50, "direction": "南北"}],
    })


def test_listing_reference_guard_is_shared_by_mixed_and_sql():
    """Natural replies must remain referable without inventing listing IDs."""
    houses = [{"id": 50}]
    assert react_agent._has_grounded_listing_ids("房源编号：50", houses)
    assert not react_agent._has_grounded_listing_ids("这套很适合你", houses)
    assert not react_agent._has_grounded_listing_ids("房源编号：51", houses)


def test_fallback_selects_relevant_complete_section():
    """A short question must not receive two unrelated full retrieved chunks."""
    answer = react_agent._relevant_evidence_excerpt("押金退还要写合同吗", [{
        "content": "## 房东入户\n不得擅自进入。\n\n## 押金退还\n应约定押金返还时间。除约定情形外无正当理由不得扣减。\n\n## 中介备案\n由机构备案。",
    }])
    assert "押金返还时间" in answer and "除约定情形外" in answer
    assert "房东入户" not in answer and "中介备案" not in answer


def test_general_stream_does_not_publish_draft_before_final_message(monkeypatch):
    """An interrupted greeting must not leak a partial model draft."""
    class BrokenAgent:
        def stream(self, *_args, **_kwargs):
            yield ("messages", (AIMessageChunk(content="半截回答"), {"langgraph_node": "model"}))
    monkeypatch.setattr(react_agent, "_get_agent_for_messages", lambda _: BrokenAgent())
    events = list(react_agent.stream_react_agent([{"role": "user", "content": "你好"}]))
    assert not any(event["type"] == "token" for event in events)
