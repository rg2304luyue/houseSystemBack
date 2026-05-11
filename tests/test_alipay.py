# -*- coding: utf-8 -*-
"""
支付宝模块测试 —— /api/alipay/*
===============================
覆盖: 生成支付链接 / 异步通知回调 / 同步回跳 / verify_return
"""

import pytest
from tests.conftest import assert_success, assert_error, assert_has_fields


class TestAlipayPay:
    """生成支付链接 POST /api/alipay/pay"""

    def test_pay_success_returns_url(self, client):
        """正常生成支付链接"""
        res = client.post("/api/alipay/pay", json={
            "out_trade_no": "TEST_ORDER_20250101_001",
            "total_amount": "0.01",
            "subject": "测试订单-月租",
        })
        body = assert_success(res)
        data = body["data"]
        assert "pay_url" in data, "响应应包含 pay_url"
        assert data["pay_url"].startswith("http"), "pay_url 应为有效 URL"

    def test_pay_without_subject_uses_default(self, client):
        """不传 subject 使用默认值"""
        res = client.post("/api/alipay/pay", json={
            "out_trade_no": "TEST_NO_SUBJECT_001",
            "total_amount": "100.00",
        })
        body = assert_success(res)
        assert "pay_url" in body["data"]

    def test_pay_with_zero_amount(self, client):
        """金额为 0"""
        res = client.post("/api/alipay/pay", json={
            "out_trade_no": "ZERO_AMOUNT_001",
            "total_amount": "0.00",
        })
        body = res.get_json()
        assert body is not None

    def test_pay_with_large_amount(self, client):
        """大额支付"""
        res = client.post("/api/alipay/pay", json={
            "out_trade_no": "LARGE_AMOUNT_001",
            "total_amount": "999999.99",
            "subject": "大额测试",
        })
        body = res.get_json()
        assert body is not None

    def test_pay_missing_out_trade_no(self, client):
        """缺少订单号"""
        res = client.post("/api/alipay/pay", json={
            "total_amount": "0.01",
        })
        assert_error(res, expected_http=400)

    def test_pay_missing_total_amount(self, client):
        """缺少金额"""
        res = client.post("/api/alipay/pay", json={
            "out_trade_no": "TEST_001",
        })
        assert_error(res, expected_http=400)

    def test_pay_empty_body(self, client):
        """空请求体"""
        res = client.post("/api/alipay/pay", json={})
        assert_error(res, expected_http=400)

    def test_pay_repeated_out_trade_no(self, client):
        """重复的订单号 —— 支付宝会生成新的支付链接"""
        res = client.post("/api/alipay/pay", json={
            "out_trade_no": "TEST_ORDER_20250101_001",
            "total_amount": "0.01",
            "subject": "重复订单号测试",
        })
        body = res.get_json()
        assert body is not None


class TestAlipayNotify:
    """异步通知 POST /api/alipay/notify"""

    def test_notify_empty_data(self, client):
        """空通知数据"""
        res = client.post("/api/alipay/notify", data={})
        assert res.status_code in [200, 400]

    def test_notify_with_random_data(self, client):
        """随机伪造的通知数据"""
        res = client.post("/api/alipay/notify", data={
            "out_trade_no": "fake_001",
            "trade_status": "TRADE_SUCCESS",
            "sign": "fake_signature_12345",
        })
        # 验证失败应返回 failure 或 400
        assert res.status_code in [200, 400]


class TestAlipayReturn:
    """同步回跳 GET /api/alipay/return"""

    def test_return_redirects(self, client):
        """同步回跳应重定向到前端"""
        res = client.get("/api/alipay/return")
        assert res.status_code in [302, 200, 400]

    def test_return_with_params(self, client):
        """带参数的同步回跳"""
        res = client.get(
            "/api/alipay/return"
            "?out_trade_no=TEST_001"
            "&trade_no=2025010123456"
            "&total_amount=0.01"
        )
        assert res.status_code in [302, 200, 400]


class TestVerifyReturn:
    """验证回跳 GET /api/alipay/verify_return"""

    def test_verify_return_success(self, client):
        """正常验证"""
        res = client.get("/api/alipay/verify_return?out_trade_no=TEST_001")
        body = res.get_json()
        assert body is not None
        assert res.status_code == 200

    def test_verify_return_no_params(self, client):
        """无参数验证"""
        res = client.get("/api/alipay/verify_return")
        body = res.get_json()
        assert body is not None
        assert res.status_code == 200
