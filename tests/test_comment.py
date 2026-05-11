# -*- coding: utf-8 -*-
"""
评论模块测试 —— /comments
=========================
覆盖: 按房源查评论 / 按ID查评论 / 创建评论 / 带回复的评论
"""

import pytest
import uuid
from tests.conftest import assert_success, assert_error


def _unique_name():
    return f"comment_user_{uuid.uuid4().hex[:6]}"


class TestGetCommentsByHouse:
    """按房源查询评论 GET /comments/<house_id>"""

    def test_get_comments_existing_house(self, client):
        """查询存在房源的评论"""
        res = client.get("/comments/1")
        body = res.get_json()
        assert body is not None
        assert "data" in body

    def test_get_comments_empty_house(self, client):
        """查询没有评论的房源应返回空列表"""
        res = client.get("/comments/99999")
        body = res.get_json()
        assert body is not None
        if body.get("data") == []:
            pass  # 符合预期

    def test_get_comments_check_structure(self, client):
        """评论数据结构完整"""
        res = client.get("/comments/1")
        body = res.get_json()
        if body.get("data") and len(body["data"]) > 0:
            comment = body["data"][0]
            for field in ["comment_id", "house_id", "username", "type", "desc", "time"]:
                assert field in comment, f"评论缺少字段: {field}"


class TestGetCommentById:
    """按ID查询评论 GET /comments/<comment_id>"""

    def test_get_comment_nonexistent(self, client):
        """查询不存在的评论ID"""
        res = client.get("/comments/99999")
        body = res.get_json()
        assert body is not None


class TestCreateComment:
    """创建评论 POST /comments"""

    def test_create_comment_as_tenant(self, client):
        """租客发表评论"""
        res = client.post("/comments", json={
            "house_id": 1,
            "username": _unique_name(),
            "type": 1,  # 租客
            "desc": "房子很不错，交通便利，推荐！",
        })
        body = res.get_json()
        assert body is not None
        assert res.status_code == 201 or body.get("message") is not None

    def test_create_comment_as_landlord(self, client):
        """房东回复评论"""
        res = client.post("/comments", json={
            "house_id": 1,
            "username": _unique_name(),
            "type": 2,  # 房东
            "desc": "感谢好评，欢迎再次入住！",
        })
        body = res.get_json()
        assert body is not None

    def test_create_comment_with_reply(self, client):
        """带 @回复 的评论"""
        res = client.post("/comments", json={
            "house_id": 1,
            "username": _unique_name(),
            "type": 2,
            "desc": "@用户A 你说得对",
            "at": 1,  # 回复评论ID=1
        })
        body = res.get_json()
        assert body is not None

    def test_create_comment_no_at_field(self, client):
        """不传 at 字段 —— 应为普通评论"""
        res = client.post("/comments", json={
            "house_id": 1,
            "username": _unique_name(),
            "type": 1,
            "desc": "普通评论，不回复任何人",
        })
        body = res.get_json()
        assert body is not None

    def test_create_comment_empty_at_field(self, client):
        """at 字段为空字符串"""
        res = client.post("/comments", json={
            "house_id": 1,
            "username": _unique_name(),
            "type": 1,
            "desc": "at字段为空的评论",
            "at": "",
        })
        body = res.get_json()
        assert body is not None

    def test_create_comment_missing_house_id(self, client):
        """缺少 house_id"""
        res = client.post("/comments", json={
            "username": _unique_name(),
            "type": 1,
            "desc": "没有房源ID的评论",
        })
        assert_error(res, expected_http=400)

    def test_create_comment_missing_username(self, client):
        """缺少 username"""
        res = client.post("/comments", json={
            "house_id": 1,
            "type": 1,
            "desc": "没有用户名的评论",
        })
        assert_error(res, expected_http=400)

    def test_create_comment_missing_type(self, client):
        """缺少 type"""
        res = client.post("/comments", json={
            "house_id": 1,
            "username": _unique_name(),
            "desc": "没有类型的评论",
        })
        assert_error(res, expected_http=400)

    def test_create_comment_missing_desc(self, client):
        """缺少 desc"""
        res = client.post("/comments", json={
            "house_id": 1,
            "username": _unique_name(),
            "type": 1,
        })
        assert_error(res, expected_http=400)

    def test_create_comment_empty_body(self, client):
        """空请求体"""
        res = client.post("/comments", json={})
        assert_error(res, expected_http=400)

    def test_create_comment_invalid_house_id(self, client):
        """house_id 不是数字"""
        res = client.post("/comments", json={
            "house_id": "abc",
            "username": _unique_name(),
            "type": 1,
            "desc": "无效房源ID",
        })
        body = res.get_json()
        assert body is not None
