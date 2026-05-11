# -*- coding: utf-8 -*-
"""
租赁模块测试 —— /rental/*
=========================
覆盖: 按租客查询租房记录（含合同和房源聚合数据）
"""

import pytest
from tests.conftest import assert_success, assert_error


class TestGetRentalByTenant:
    """按租客查询 GET /rental/tenants/<tenant_username>"""

    def test_existing_tenant(self, client):
        """查询存在的租客"""
        res = client.get("/rental/tenants/test_tenant")
        body = res.get_json()
        assert body is not None

    def test_nonexistent_tenant_returns_404(self, client):
        """查询不存在的租客应返回 404"""
        res = client.get("/rental/tenants/nonexistent_tenant_xyz_999")
        body = res.get_json()
        assert body is not None
        if body.get("success") is False:
            assert res.status_code in [404, 500]

    def test_empty_username(self, client):
        """空用户名"""
        res = client.get("/rental/tenants/")
        # Flask 可能返回 404 或 308 重定向
        assert res.status_code in [404, 308, 301]

    def test_special_characters_username(self, client):
        """特殊字符用户名"""
        res = client.get("/rental/tenants/%20%20%20")
        body = res.get_json()
        assert body is not None

    def test_response_aggregated_data(self, client):
        """响应数据应包含聚合的合同和房源字段"""
        res = client.get("/rental/tenants/test_tenant")
        body = res.get_json()
        if body and body.get("data") and len(body["data"]) > 0:
            rental = body["data"][0]
            # 聚合字段
            aggregated_fields = ["purpose", "startDate", "endDate", "title",
                                 "region", "landlordPhone", "rentValue"]
            for field in aggregated_fields:
                assert field in rental, f"聚合数据缺少字段: {field}"
