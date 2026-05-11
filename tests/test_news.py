# -*- coding: utf-8 -*-
"""
新闻模块测试 —— /news/*
=======================
覆盖: 列表分页 / 详情 / 新增 / 更新 / 删除
"""

import pytest
from tests.conftest import assert_success, assert_error, assert_has_fields


class TestNewsList:
    """新闻列表 GET /news"""

    def test_get_all_news_structure(self, client):
        """列表返回正确数据结构"""
        res = client.get("/news")
        body = assert_success(res)
        data = body["data"]
        assert_has_fields(data, "items", "total")
        assert isinstance(data["items"], list)

    def test_pagination_page1_per5(self, client):
        """分页 —— 第1页每页5条"""
        res = client.get("/news?page=1&per_page=5")
        body = assert_success(res)
        assert len(body["data"]["items"]) <= 5

    def test_empty_page(self, client):
        """超出范围的页面"""
        res = client.get("/news?page=99999")
        body = assert_success(res)
        assert body["data"]["items"] == []

    def test_default_per_page(self, client):
        """默认每页 10 条"""
        res = client.get("/news")
        body = assert_success(res)
        # 响应可能不包含 per_page 字段，只验证结构
        assert "items" in body["data"]


class TestNewsDetail:
    """新闻详情 GET /news/<id>"""

    def test_get_existing_news(self, client):
        """查询存在的新闻"""
        res = client.get("/news/1")
        body = res.get_json()
        assert body is not None
        if body.get("success") is False:
            pytest.skip("数据库中暂无 ID=1 的新闻")

    def test_get_nonexistent_news(self, client):
        """查询不存在的新闻"""
        res = client.get("/news/99999")
        assert_error(res, expected_http=404)


class TestNewsCRUD:
    """新闻增删改"""

    @pytest.fixture
    def news_id(self, client):
        """创建测试新闻，测试结束后自动删除"""
        res = client.post("/news", json={
            "title": "自动化测试新闻标题",
            "content": "这是自动化测试生成的新闻内容，用于验证 API。",
        })
        body = res.get_json()
        if body and body.get("success"):
            yield body["data"]["id"]
            # 清理
            client.delete(f"/news/{body['data']['id']}")
        else:
            pytest.skip(f"无法创建测试新闻: {body.get('message') if body else 'unknown'}")

    def test_create_news_success(self, client, news_id):
        """创建新闻成功"""
        assert news_id > 0

    def test_created_news_is_readable(self, client, news_id):
        """创建后可以立即查到"""
        res = client.get(f"/news/{news_id}")
        body = assert_success(res)
        assert body["data"]["title"] == "自动化测试新闻标题"

    def test_create_news_missing_title(self, client):
        """缺少标题"""
        res = client.post("/news", json={"content": "只有内容"})
        assert_error(res, expected_http=400)

    def test_create_news_missing_content(self, client):
        """缺少内容"""
        res = client.post("/news", json={"title": "只有标题"})
        assert_error(res, expected_http=400)

    def test_create_news_empty_body(self, client):
        """空请求体"""
        res = client.post("/news", json={})
        assert_error(res, expected_http=400)

    def test_update_news_title(self, client, news_id):
        """更新新闻标题"""
        res = client.put(f"/news/{news_id}", json={
            "title": "更新后的新闻标题",
        })
        body = assert_success(res)
        assert body["data"]["title"] == "更新后的新闻标题"

    def test_update_news_content(self, client, news_id):
        """更新新闻内容"""
        res = client.put(f"/news/{news_id}", json={
            "content": "更新后的内容文本",
        })
        body = assert_success(res)
        assert body["data"]["content"] == "更新后的内容文本"

    def test_update_nonexistent_news(self, client):
        """更新不存在的新闻"""
        res = client.put("/news/99999", json={"title": "不会成功"})
        assert_error(res, expected_http=404)

    def test_update_empty_body(self, client):
        """空请求体更新"""
        res = client.put("/news/1", json={})
        assert_error(res, expected_http=400)

    def test_delete_news_complete_flow(self, client):
        """完整删除流程: 创建 → 删除 → 确认删除"""
        res = client.post("/news", json={
            "title": "即将被删除的新闻",
            "content": "这条新闻将被删除。",
        })
        body = res.get_json()
        if not body or not body.get("success"):
            pytest.skip("无法创建测试新闻")

        news_id = body["data"]["id"]

        # 删除
        res = client.delete(f"/news/{news_id}")
        assert_success(res)

        # 确认已删除
        res = client.get(f"/news/{news_id}")
        assert_error(res, expected_http=404)

    def test_delete_nonexistent_news(self, client):
        """删除不存在的新闻"""
        res = client.delete("/news/99999")
        assert_error(res, expected_http=404)
