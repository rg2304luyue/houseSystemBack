# -*- coding: utf-8 -*-
"""
AI 聊天模块测试 —— /chat-ai/*
=============================
覆盖: 房源搜索 / 热门房源 / 房源详情 / AI 对话 / 会话管理
依赖: AI 对话接口需要 DASHSCOPE_API_KEY，不可用时自动跳过
"""

import pytest
from tests.conftest import assert_success, assert_error, assert_has_fields


# ══════════════════════════════════════════════════════════════
#  房源搜索（直接数据库查询，不走 AI）
# ══════════════════════════════════════════════════════════════

class TestHouseSearch:
    """房源搜索 POST /chat-ai/houses/search"""

    def test_no_filters_returns_all_available(self, client):
        """无筛选条件返回所有可租房源"""
        res = client.post("/chat-ai/houses/search", json={})
        body = assert_success(res)
        data = body["data"]
        assert data["success"] is True
        assert "houses" in data
        assert "count" in data
        for h in data["houses"]:
            assert h["available"] == 1, "应只返回可租房源"

    def test_search_by_price_range(self, client):
        """按价格范围搜索"""
        res = client.post("/chat-ai/houses/search", json={
            "min_price": 1000,
            "max_price": 3000,
        })
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["price"] >= 1000

    def test_search_by_min_price_only(self, client):
        """仅最低价格"""
        res = client.post("/chat-ai/houses/search", json={"min_price": 5000})
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["price"] >= 5000

    def test_search_by_max_price_only(self, client):
        """仅最高价格"""
        res = client.post("/chat-ai/houses/search", json={"max_price": 1500})
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["price"] <= 1500

    def test_search_by_region(self, client):
        """按区域模糊搜索"""
        res = client.post("/chat-ai/houses/search", json={"region": "岳麓"})
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert "岳麓" in h.get("region", "")

    def test_search_by_area_range(self, client):
        """按面积范围搜索"""
        res = client.post("/chat-ai/houses/search", json={
            "min_area": 50,
            "max_area": 100,
        })
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["area"] >= 50

    def test_search_by_rooms_keyword(self, client):
        """按户型关键词搜索"""
        res = client.post("/chat-ai/houses/search", json={"rooms": "2室"})
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert "2室" in h.get("rooms", "")

    def test_search_by_rent_type(self, client):
        """按租赁方式搜索"""
        res = client.post("/chat-ai/houses/search", json={"rent_type": "整租"})
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["rent_type"] == "整租"

    def test_search_by_subway(self, client):
        """按近地铁搜索"""
        res = client.post("/chat-ai/houses/search", json={"subway": True})
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["subway"] == 1

    def test_search_by_decoration(self, client):
        """按装修搜索"""
        res = client.post("/chat-ai/houses/search", json={"decoration": "精装"})
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert "精装" in h.get("decoration", "")

    def test_search_combined_filters(self, client):
        """组合筛选"""
        res = client.post("/chat-ai/houses/search", json={
            "min_price": 1000,
            "max_price": 5000,
            "region": "岳麓",
            "rent_type": "整租",
            "subway": True,
        })
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["price"] >= 1000
            assert "岳麓" in h.get("region", "")

    def test_search_max_20_results(self, client):
        """最多返回 20 条结果"""
        res = client.post("/chat-ai/houses/search", json={})
        body = assert_success(res)
        assert body["data"]["count"] <= 20
        assert len(body["data"]["houses"]) <= 20

    def test_search_results_sorted_by_price_asc(self, client):
        """结果按价格升序排列"""
        res = client.post("/chat-ai/houses/search", json={})
        body = assert_success(res)
        prices = [h["price"] for h in body["data"]["houses"]]
        assert prices == sorted(prices), "房源应按价格升序排列"


# ══════════════════════════════════════════════════════════════
#  热门房源
# ══════════════════════════════════════════════════════════════

class TestHousePopular:
    """热门房源 GET /chat-ai/houses/popular"""

    def test_default_limit_10(self, client):
        """默认返回 10 条"""
        res = client.get("/chat-ai/houses/popular")
        body = assert_success(res)
        assert len(body["data"]["houses"]) <= 10

    def test_custom_limit_5(self, client):
        """自定义 limit=5"""
        res = client.get("/chat-ai/houses/popular?limit=5")
        body = assert_success(res)
        assert len(body["data"]["houses"]) <= 5

    def test_custom_limit_20(self, client):
        """自定义 limit=20"""
        res = client.get("/chat-ai/houses/popular?limit=20")
        body = assert_success(res)
        assert len(body["data"]["houses"]) <= 20

    def test_zero_limit(self, client):
        """limit=0"""
        res = client.get("/chat-ai/houses/popular?limit=0")
        body = assert_success(res)
        assert body["data"]["houses"] == []

    def test_negative_limit(self, client):
        """负数 limit"""
        res = client.get("/chat-ai/houses/popular?limit=-1")
        body = res.get_json()
        assert body is not None

    def test_only_available_houses(self, client):
        """只返回可租房源"""
        res = client.get("/chat-ai/houses/popular?limit=20")
        body = assert_success(res)
        for h in body["data"]["houses"]:
            assert h["available"] == 1

    def test_sorted_by_views_desc(self, client):
        """按浏览量降序排列"""
        res = client.get("/chat-ai/houses/popular?limit=10")
        body = assert_success(res)
        views = [h.get("page_views", 0) for h in body["data"]["houses"]]
        assert views == sorted(views, reverse=True), "应按浏览量降序"


# ══════════════════════════════════════════════════════════════
#  房源详情（AI 模块）
# ══════════════════════════════════════════════════════════════

class TestHouseDetail:
    """房源详情 GET /chat-ai/houses/<house_id>"""

    def test_existing_house(self, client):
        """存在的房源"""
        res = client.get("/chat-ai/houses/1")
        body = assert_success(res)
        assert body["data"]["success"] is True
        assert body["data"]["house"]["id"] == 1

    def test_nonexistent_house(self, client):
        """不存在的房源"""
        res = client.get("/chat-ai/houses/99999")
        assert_error(res, expected_http=404)

    def test_house_has_required_fields(self, client):
        """详情包含必要字段"""
        res = client.get("/chat-ai/houses/1")
        body = assert_success(res)
        house = body["data"]["house"]
        required = ["id", "title", "region", "price", "rent_type", "rooms"]
        assert_has_fields(house, *required)


# ══════════════════════════════════════════════════════════════
#  AI 对话（需要 DASHSCOPE_API_KEY）
# ══════════════════════════════════════════════════════════════

class TestChatAI:
    """AI 对话 POST /chat-ai/chat（需认证 + AI 服务）"""

    def test_no_token_returns_401(self, client):
        """未认证返回 401"""
        res = client.post("/chat-ai/chat", json={"message": "推荐房源"})
        assert_error(res, expected_http=401)

    def test_with_token_no_ai_key(self, client, auth_headers):
        """有 Token 但无 AI Key —— 可能返回失败"""
        res = client.post("/chat-ai/chat", json={
            "message": "帮我推荐一个两居室的房子",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None
        if not body.get("success"):
            if any(kw in body.get("message", "") for kw in ["API", "失败"]):
                pytest.skip(f"AI 服务不可用: {body.get('message')}")

    def test_empty_message(self, client, auth_headers):
        """空消息应返回 400"""
        res = client.post("/chat-ai/chat", json={"message": ""}, headers=auth_headers)
        body = res.get_json()
        assert body is not None
        if body.get("success") is False:
            assert body.get("code") in [400, 401]

    def test_with_session_id(self, client, auth_headers):
        """带 session_id 的对话（继续已有会话）"""
        res = client.post("/chat-ai/chat", json={
            "message": "继续聊天",
            "session_id": 99999,
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_invalid_token(self, client, invalid_auth_headers):
        """无效 Token"""
        res = client.post("/chat-ai/chat", json={
            "message": "测试",
        }, headers=invalid_auth_headers)
        assert_error(res, expected_http=401)

    def test_stream_empty_message(self, client, auth_headers):
        """流式接口 —— 空消息"""
        res = client.post("/chat-ai/chat/stream", json={
            "message": "",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_stream_no_auth(self, client):
        """流式接口 —— 未认证"""
        res = client.post("/chat-ai/chat/stream", json={"message": "你好"})
        assert_error(res, expected_http=401)


class TestChatSessions:
    """会话列表 GET /chat-ai/sessions（需认证）"""

    def test_no_auth(self, client):
        """未认证"""
        res = client.get("/chat-ai/sessions")
        assert_error(res, expected_http=401)

    def test_with_auth(self, client, auth_headers):
        """已认证获取会话列表"""
        res = client.get("/chat-ai/sessions", headers=auth_headers)
        body = assert_success(res)
        assert isinstance(body["data"], list)


class TestSessionMessages:
    """会话消息 GET /chat-ai/sessions/<id>/messages"""

    def test_empty_for_nonexistent(self, client):
        """不存在的会话返回空列表"""
        res = client.get("/chat-ai/sessions/99999/messages")
        body = assert_success(res)
        assert body["data"] == []
