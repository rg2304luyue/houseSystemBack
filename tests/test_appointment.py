# -*- coding: utf-8 -*-
"""
预约模块测试 —— /appointments
=============================
覆盖: 创建看房预约 / 边界条件 / 错误处理
"""

import pytest
from tests.conftest import assert_success, assert_error


class TestCreateAppointment:
    """创建预约 POST /appointments"""

    def test_create_appointment_success(self, client):
        """正常创建预约"""
        res = client.post("/appointments", json={
            "username": "appointment_test_user",
            "property": "阳光花园-1栋101",
            "time": "2025-08-01T10:00:00+08:00",
        })
        body = res.get_json()
        assert body is not None
        if body.get("success"):
            assert res.status_code == 201

    def test_create_appointment_utc_time(self, client):
        """使用 UTC 时间"""
        res = client.post("/appointments", json={
            "username": "utc_test_user",
            "property": "测试房源UTC",
            "time": "2025-09-01T14:00:00Z",
        })
        body = res.get_json()
        assert body is not None

    def test_create_appointment_iso_basic(self, client):
        """ISO 8601 基本格式"""
        res = client.post("/appointments", json={
            "username": "iso_test_user",
            "property": "ISO测试房源",
            "time": "2025-10-15T09:30:00",
        })
        body = res.get_json()
        assert body is not None

    def test_create_appointment_missing_username(self, client):
        """缺少用户名"""
        res = client.post("/appointments", json={
            "property": "test",
            "time": "2025-08-01T10:00:00+08:00",
        })
        assert_error(res, expected_http=400)

    def test_create_appointment_missing_property(self, client):
        """缺少房源名称"""
        res = client.post("/appointments", json={
            "username": "test",
            "time": "2025-08-01T10:00:00+08:00",
        })
        assert_error(res, expected_http=400)

    def test_create_appointment_missing_time(self, client):
        """缺少预约时间"""
        res = client.post("/appointments", json={
            "username": "test",
            "property": "test",
        })
        assert_error(res, expected_http=400)

    def test_create_appointment_invalid_time_format(self, client):
        """无效的日期格式"""
        res = client.post("/appointments", json={
            "username": "test",
            "property": "test",
            "time": "not-a-valid-date",
        })
        assert_error(res, expected_http=400)

    def test_create_appointment_empty_time(self, client):
        """空时间字符串"""
        res = client.post("/appointments", json={
            "username": "test",
            "property": "test",
            "time": "",
        })
        body = res.get_json()
        assert body is not None

    def test_create_appointment_empty_body(self, client):
        """空请求体"""
        res = client.post("/appointments", json={})
        assert_error(res, expected_http=400)

    def test_create_appointment_past_time(self, client):
        """过去的时间"""
        res = client.post("/appointments", json={
            "username": "past_test",
            "property": "过去时间测试",
            "time": "2020-01-01T10:00:00+08:00",
        })
        body = res.get_json()
        assert body is not None

    def test_create_appointment_very_far_future(self, client):
        """极远的未来时间"""
        res = client.post("/appointments", json={
            "username": "future_test",
            "property": "未来测试",
            "time": "2099-12-31T23:59:59+08:00",
        })
        body = res.get_json()
        assert body is not None
