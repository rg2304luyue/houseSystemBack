"""Regression coverage for natural rental-search follow-ups."""

import json
from unittest.mock import MagicMock

import pytest

from app.services.query_constraints import (
    extract_house_constraints,
    get_search_clarification,
    merge_house_constraints,
    recent_house_ids,
)
from app.services.query_router import QueryRoute, route_query


@pytest.mark.parametrize("query", ["谢谢", "好的谢谢你", "你好", "再见"])
def test_social_turn_does_not_repeat_search(query):
    """Social turns must not inherit the preceding inventory route."""
    assert route_query(query, ["岳麓区1500元以内的房源"]) is QueryRoute.GENERAL


@pytest.mark.parametrize("query", ["换一批", "贵一点也行", "便宜些", "只要整租"])
def test_search_followup_keeps_inventory_route(query):
    """Natural updates remain inventory requests when search context exists."""
    assert route_query(query, ["岳麓区1500元以内的房源"]) is QueryRoute.SQL


def test_rent_type_update_retains_previous_budget_and_region():
    """Changing rental type must retain unrelated explicit conditions."""
    result = merge_house_constraints(["岳麓区1500元以内", "只要整租"])
    assert result.region == "岳麓"
    assert result.max_price == 1500
    assert result.rent_type == "整租"


@pytest.mark.parametrize("query", ["装修不限", "户型不限", "区域不限"])
def test_unrelated_unlimited_filter_does_not_clear_budget_or_area(query):
    """Removing one preference must not silently relax price and area."""
    result = merge_house_constraints(["预算1500元，面积60平方米以上", query])
    assert result.max_price == 1500
    assert result.min_area == 60


def test_explicit_budget_removal_preserves_area():
    """Removing the price ceiling is independent of the area constraint."""
    result = merge_house_constraints(["1500元以内，60平方米以上", "预算不限"])
    assert result.max_price is None
    assert result.min_area == 60


def test_approximate_budget_is_not_parsed_as_hard_ceiling():
    """Adding the word budget must not change existing approximate semantics."""
    assert extract_house_constraints("预算1500元左右") == extract_house_constraints("1500元左右")


def test_relative_budget_requires_clarification_and_keeps_constraints():
    """An unquantified budget change cannot invent a new permitted ceiling."""
    messages = ["岳麓区1500元以内", "只要整租", "贵一点也行"]
    assert get_search_clarification(messages)
    assert merge_house_constraints(messages).max_price == 1500
    assert merge_house_constraints(messages).rent_type == "整租"


def test_explicit_new_budget_does_not_require_clarification():
    """The user's stated replacement amount is sufficient to resume search."""
    assert get_search_clarification(["1500元以内", "贵一点也行，最多2000元"]) is None


@pytest.mark.parametrize("query", ["谢谢", "好的谢谢你", "你好", "再见"])
def test_social_reply_does_not_trigger_budget_clarification(query):
    """A prior price adjustment cannot force subsequent social clarification."""
    assert get_search_clarification(["贵一点也行", query]) is None


def test_recent_house_ids_only_uses_latest_display_and_deduplicates():
    """Exclusions use the most recent display rather than older suggestions."""
    assert recent_house_ids([
        {"role": "assistant", "content": "房源ID 1"},
        {"role": "assistant", "content": "房源编号：2，房源 ID 3，房源ID 2"},
        {"role": "assistant", "content": "不客气"},
        {"role": "user", "content": "换一批，房源ID 999"},
    ]) == [2, 3]


def test_search_excludes_previous_ids_in_sql_without_changing_filter_contract(monkeypatch):
    """Repeat-search exclusion is applied before both count and result fetch."""
    from app.services import react_tools

    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.count.return_value = 0
    query.all.return_value = []
    context = MagicMock()
    context.__enter__.return_value.query.return_value = query
    monkeypatch.setattr(react_tools, "SessionLocal", MagicMock(return_value=context))
    payload = json.loads(react_tools.search_houses_by_criteria.invoke({"exclude_ids": [2, 3, 2]}))
    assert payload["excluded_ids"] == [2, 3]
    assert "excluded_ids" not in payload["applied_filters"]
    exclusion = query.filter.call_args_list[1].args[0]
    compiled = exclusion.compile(compile_kwargs={"literal_binds": True})
    assert "NOT IN (2, 3)" in str(compiled)


@pytest.mark.parametrize("excluded_ids", [[0], [-1], [True], list(range(1, 102))])
def test_invalid_exclusion_ids_do_not_open_database(monkeypatch, excluded_ids):
    """Invalid or unbounded exclusions fail before making database queries."""
    from app.services import react_tools

    session = MagicMock()
    monkeypatch.setattr(react_tools, "SessionLocal", session)
    payload = json.loads(react_tools.search_houses_by_criteria.func(exclude_ids=excluded_ids))
    assert "error" in payload
    session.assert_not_called()


@pytest.mark.parametrize("reset", ["重新开始找房", "清空条件", "忘掉之前条件"])
def test_explicit_reset_clears_constraints_and_displayed_ids(reset):
    """An explicit fresh search must not revive earlier preferences or results."""
    messages = [
        {"role": "user", "content": "岳麓区1500元以内，只要整租"},
        {"role": "assistant", "content": "房源ID 12"},
        {"role": "user", "content": reset},
    ]
    assert not merge_house_constraints(messages).has_filters
    assert recent_house_ids(messages) == []


def test_reset_can_include_new_conditions():
    """The reset turn itself may supply replacement search criteria."""
    result = merge_house_constraints(["岳麓区1500元以内", "重新开始找房，雨花区2000元以内"])
    assert result.region == "雨花"
    assert result.max_price == 2000


@pytest.mark.parametrize("query", ["第二套押金多少", "第2套合同怎么签", "这套的押金呢"])
def test_listing_specific_policy_question_uses_both_sources(query):
    """Listing policy questions need live facts as well as general guidance."""
    assert route_query(query, ["推荐岳麓区房源"]) is QueryRoute.MIXED


def test_bare_number_answers_specific_budget_question_without_losing_conditions():
    """A number only becomes a budget in response to our exact budget prompt."""
    result = merge_house_constraints([
        {"role": "user", "content": "岳麓区1500元以内，只要整租"},
        {"role": "user", "content": "贵一点也行"},
        {"role": "assistant", "content": "每月租金最多能接受多少元？我会保留你之前的其他找房条件。"},
        {"role": "user", "content": "1800"},
    ])
    assert result.max_price == 1800
    assert result.region == "岳麓"
    assert result.rent_type == "整租"
    assert not merge_house_constraints(["1800"]).has_filters


@pytest.mark.parametrize("query,expected", [("只要合租，不要整租", "合租"), ("不要合租，要整租", "整租"), ("整租改成合租", "合租")])
def test_negated_rental_type_does_not_override_requested_type(query, expected):
    """Negated and corrected rental entities must preserve positive intent."""
    assert extract_house_constraints(query).rent_type == expected


@pytest.mark.parametrize("query", ["不要岳麓区，换雨花区", "岳麓区改成雨花区", "只看雨花区，不考虑岳麓区"])
def test_region_correction_uses_positive_destination(query):
    """A rejected region cannot replace the user's requested destination."""
    assert extract_house_constraints(query).region == "雨花"
    assert get_search_clarification([query]) is None


@pytest.mark.parametrize("query", ["岳麓区或者雨花区都行", "雨花区和天心区找房"])
def test_multiple_regions_need_clarification(query):
    """Unsupported region alternatives require a choice before executing SQL."""
    assert get_search_clarification([query])
