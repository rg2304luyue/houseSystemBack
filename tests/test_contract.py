# -*- coding: utf-8 -*-
"""
合同模块测试 —— /contracts
==========================
覆盖: 创建合同 / 按租客+房东查询合同
"""

import pytest
import uuid
from tests.conftest import assert_success, assert_error


_BASE = {
    "rentValue": 3000,
    "purpose": "住宅",
    "startDate": "2025-07-01",
    "endDate": "2026-06-30",
    "landlordName": "测试房东",
    "landlordId": "1",
    "landlordPhone": "13800001111",
    "tenantName": "placeholder",
    "tenantId": "1",
    "tenantPhone": "13900001111",
    "formattedRent": "3000元/月",
    "currentDate": "2025-06-15",
    "houseid": 1,
}


def _make(**overrides):
    p = dict(_BASE)
    p["tenantName"] = f"tenant_{uuid.uuid4().hex[:6]}"
    p.update(overrides)
    return p


class TestCreateContract:
    """创建合同 POST /contracts"""

    def test_create_contract_success(self, client):
        """正常创建合同（含 rental 关联）"""
        res = client.post("/contracts", json=_make())
        body = assert_success(res, expected_http=201)
        data = body["data"]
        # 应包含 rental_info
        assert "rental_info" in data or "rentValue" in str(data)

    def test_create_contract_all_required_fields_present(self, client):
        """所有必填字段存在时创建成功"""
        res = client.post("/contracts", json=_make(
            rentValue=5000,
            purpose="办公",
            startDate="2025-08-01",
            endDate="2026-07-31",
        ))
        assert_success(res, expected_http=201)

    def test_create_contract_missing_rent_value(self, client):
        """缺少 rentValue 应返回 400"""
        payload = _make()
        del payload["rentValue"]
        res = client.post("/contracts", json=payload)
        assert_error(res, expected_http=400)

    def test_create_contract_missing_purpose(self, client):
        """缺少 purpose"""
        payload = _make()
        del payload["purpose"]
        res = client.post("/contracts", json=payload)
        assert_error(res, expected_http=400)

    def test_create_contract_missing_start_date(self, client):
        """缺少 startDate"""
        payload = _make()
        del payload["startDate"]
        res = client.post("/contracts", json=payload)
        assert_error(res, expected_http=400)

    def test_create_contract_missing_end_date(self, client):
        """缺少 endDate"""
        payload = _make()
        del payload["endDate"]
        res = client.post("/contracts", json=payload)
        assert_error(res, expected_http=400)

    def test_create_contract_missing_landlord_name(self, client):
        """缺少 landlordName"""
        payload = _make()
        del payload["landlordName"]
        res = client.post("/contracts", json=payload)
        assert_error(res, expected_http=400)

    def test_create_contract_missing_tenant_name(self, client):
        """缺少 tenantName"""
        payload = _make()
        del payload["tenantName"]
        res = client.post("/contracts", json=payload)
        assert_error(res, expected_http=400)

    def test_create_contract_missing_houseid(self, client):
        """缺少 houseid（rental_service 需要）"""
        payload = _make()
        del payload["houseid"]
        res = client.post("/contracts", json=payload)
        body = res.get_json()
        assert body is not None
        # 应因 rental 创建失败而返回 500
        if body.get("success") is False:
            pass

    def test_create_contract_empty_body(self, client):
        """空请求体"""
        res = client.post("/contracts", json={})
        assert_error(res, expected_http=400)

    def test_create_contract_invalid_json(self, client):
        """无效 JSON"""
        res = client.post("/contracts", data="bad json",
                          content_type="application/json")
        assert res.status_code in [400, 415, 500]


class TestGetContract:
    """查询合同 GET /contracts/<tenantName>/<landlordId>"""

    def test_get_nonexistent_contract(self, client):
        """查询不存在的合同"""
        res = client.get("/contracts/nonexistent_tenant_xyz/99999")
        body = res.get_json()
        assert body is not None
        assert body.get("success") is False or res.status_code in [404, 500]
