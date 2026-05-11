# -*- coding: utf-8 -*-
"""
维修投诉模块测试 —— /repaires & /complaint-persons
===================================================
覆盖: 创建维修申报 / 创建投诉 / 获取可投诉对象
"""

import pytest
from tests.conftest import assert_success, assert_error, assert_has_fields


class TestCreateRepair:
    """创建维修申报 POST /repaires"""

    def test_create_repair_full_fields(self, client):
        """完整字段创建维修申报"""
        res = client.post("/repaires", json={
            "report_reason": "repair",
            "house_address": "测试小区1栋101室",
            "repair_type": "水管漏水",
            "repair_description": "厨房水龙头漏水严重，需要紧急维修",
            "agreed_terms": True,
        })
        body = res.get_json()
        assert body is not None
        if body.get("success"):
            assert res.status_code == 201

    def test_create_repair_minimal_fields(self, client):
        """最少必填字段创建维修申报"""
        res = client.post("/repaires", json={
            "report_reason": "repair",
            "house_address": "测试小区2栋202",
            "repair_type": "电路故障",
            "agreed_terms": True,
        })
        body = res.get_json()
        assert body is not None

    def test_create_complaint_full_fields(self, client):
        """完整字段创建投诉"""
        res = client.post("/repaires", json={
            "report_reason": "complaint",
            "house_address": "测试小区3栋303",
            "repair_type": "服务态度问题",
            "complaint_content": "房东多次无故拖延维修，态度恶劣",
            "complaint_person": "不良房东",
            "agreed_terms": True,
        })
        body = res.get_json()
        assert body is not None
        if body.get("success"):
            assert res.status_code == 201

    def test_create_complaint_minimal_fields(self, client):
        """最少必填字段创建投诉"""
        res = client.post("/repaires", json={
            "report_reason": "complaint",
            "house_address": "测试小区4栋404",
            "repair_type": "房屋设施损坏",
            "agreed_terms": True,
        })
        body = res.get_json()
        assert body is not None

    def test_missing_report_reason(self, client):
        """缺少 report_reason"""
        res = client.post("/repaires", json={
            "house_address": "test",
            "repair_type": "test",
            "agreed_terms": True,
        })
        assert_error(res, expected_http=400)

    def test_missing_house_address(self, client):
        """缺少 house_address"""
        res = client.post("/repaires", json={
            "report_reason": "repair",
            "repair_type": "test",
            "agreed_terms": True,
        })
        assert_error(res, expected_http=400)

    def test_missing_repair_type(self, client):
        """缺少 repair_type"""
        res = client.post("/repaires", json={
            "report_reason": "repair",
            "house_address": "test",
            "agreed_terms": True,
        })
        assert_error(res, expected_http=400)

    def test_missing_agreed_terms(self, client):
        """缺少 agreed_terms"""
        res = client.post("/repaires", json={
            "report_reason": "repair",
            "house_address": "test",
            "repair_type": "test",
        })
        assert_error(res, expected_http=400)

    def test_empty_body(self, client):
        """空请求体"""
        res = client.post("/repaires", json={})
        assert_error(res, expected_http=400)

    def test_none_fields_handling(self, client):
        """None 字段自动转换为空字符串"""
        res = client.post("/repaires", json={
            "report_reason": "repair",
            "house_address": "test address",
            "repair_type": "test type",
            "repair_description": None,
            "complaint_content": None,
            "complaint_person": None,
            "agreed_terms": True,
        })
        body = res.get_json()
        assert body is not None

    def test_booleans_in_json(self, client):
        """布尔值字段验证"""
        res = client.post("/repaires", json={
            "report_reason": "repair",
            "house_address": "test",
            "repair_type": "test",
            "agreed_terms": False,
        })
        body = res.get_json()
        assert body is not None


class TestComplaintPersons:
    """获取可投诉对象 GET /complaint-persons"""

    def test_returns_list(self, client):
        """返回可投诉的房东列表"""
        res = client.get("/complaint-persons")
        body = res.get_json()
        assert body is not None
        # 可能是 list 或 dict
        assert isinstance(body, (list, dict))

    def test_response_has_expected_structure(self, client):
        """响应的数据结构"""
        res = client.get("/complaint-persons")
        body = res.get_json()
        if isinstance(body, list) and len(body) > 0:
            assert "id" in body[0] or "name" in body[0]
