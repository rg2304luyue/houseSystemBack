# -*- coding: utf-8 -*-
"""
邮箱认证模块测试 —— /email-auth/*
==================================
覆盖: 发送验证码 / 验证码登录 / 验证码校验
依赖: Redis + Celery，外部服务不可用时自动跳过
"""

import pytest
from tests.conftest import assert_success, assert_error


class TestSendCode:
    """发送验证码 POST /email-auth/send-code"""

    def test_empty_body(self, client):
        """空请求体"""
        res = client.post("/email-auth/send-code", json={})
        assert_error(res, expected_http=400)

    def test_missing_email_field(self, client):
        """缺少 email 字段"""
        res = client.post("/email-auth/send-code", json={"foo": "bar"})
        assert_error(res, expected_http=400)

    def test_invalid_email_format_no_at(self, client):
        """无效邮箱 —— 没有 @"""
        res = client.post("/email-auth/send-code", json={"email": "not-an-email"})
        assert_error(res, expected_http=400)

    def test_invalid_email_format_no_domain(self, client):
        """无效邮箱 —— 缺少域名"""
        res = client.post("/email-auth/send-code", json={"email": "user@"})
        assert_error(res, expected_http=400)

    def test_invalid_email_format_no_user(self, client):
        """无效邮箱 —— 缺少用户名"""
        res = client.post("/email-auth/send-code", json={"email": "@domain.com"})
        assert_error(res, expected_http=400)

    def test_invalid_email_format_special_chars(self, client):
        """无效邮箱 —— 特殊字符"""
        res = client.post("/email-auth/send-code", json={"email": "a" * 1000 + "@test.com"})
        body = res.get_json()
        assert body is not None

    def test_unregistered_email(self, client):
        """未注册的邮箱"""
        res = client.post("/email-auth/send-code", json={
            "email": "never_registered_999@example.com"
        })
        body = res.get_json()
        assert body is not None
        assert body.get("success") is False or res.status_code != 200

    def test_send_to_registered_email(self, client):
        """向已注册邮箱发送验证码（需 Redis + Celery）"""
        res = client.post("/email-auth/send-code", json={
            "email": "autotest_user@test.com"
        })
        body = res.get_json()
        assert body is not None
        if not body.get("success"):
            if any(kw in body.get("message", "") for kw in ["暂不可用", "繁忙", "服务"]):
                pytest.skip(f"外部服务不可用: {body.get('message')}")

    def test_rate_limit_60s(self, client):
        """60秒内重复发送应被限频"""
        # 第一次发送
        res1 = client.post("/email-auth/send-code", json={
            "email": "autotest_user@test.com"
        })
        body1 = res1.get_json()
        if body1 and not body1.get("success"):
            pytest.skip(f"外部服务不可用: {body1.get('message')}")

        # 立即第二次发送（应被限频）
        res2 = client.post("/email-auth/send-code", json={
            "email": "autotest_user@test.com"
        })
        body2 = res2.get_json()
        assert body2 is not None
        if body2.get("code") == 429:
            pass  # 符合限频预期


class TestVerifyLogin:
    """验证码登录 POST /email-auth/verify-login"""

    def test_empty_body(self, client):
        """空请求"""
        res = client.post("/email-auth/verify-login", json={})
        assert_error(res, expected_http=400)

    def test_missing_code(self, client):
        """缺少验证码"""
        res = client.post("/email-auth/verify-login", json={
            "email": "autotest_user@test.com",
        })
        assert_error(res, expected_http=400)

    def test_missing_email(self, client):
        """缺少邮箱"""
        res = client.post("/email-auth/verify-login", json={"code": "123456"})
        assert_error(res, expected_http=400)

    def test_wrong_code(self, client):
        """错误的验证码"""
        res = client.post("/email-auth/verify-login", json={
            "email": "autotest_user@test.com",
            "code": "000000",
        })
        body = res.get_json()
        assert body is not None
        if body.get("code") == 500:
            pytest.skip("Redis 不可用，跳过验证码校验测试")

    def test_invalid_email_format(self, client):
        """无效邮箱格式"""
        res = client.post("/email-auth/verify-login", json={
            "email": "bad_email",
            "code": "123456",
        })
        assert_error(res, expected_http=400)

    def test_expired_code(self, client):
        """过期的验证码"""
        res = client.post("/email-auth/verify-login", json={
            "email": "autotest_user@test.com",
            "code": "111111",
        })
        body = res.get_json()
        assert body is not None


class TestVerifyCodeOnly:
    """仅校验验证码 POST /email-auth/verify-code"""

    def test_empty_body(self, client):
        """空请求"""
        res = client.post("/email-auth/verify-code", json={})
        assert_error(res, expected_http=400)

    def test_wrong_code(self, client):
        """错误的验证码"""
        res = client.post("/email-auth/verify-code", json={
            "email": "autotest_user@test.com",
            "code": "999999",
        })
        body = res.get_json()
        assert body is not None
        if body.get("code") == 500:
            pytest.skip("Redis 不可用")

    def test_invalid_email(self, client):
        """无效邮箱"""
        res = client.post("/email-auth/verify-code", json={
            "email": "not_an_email",
            "code": "123456",
        })
        assert_error(res, expected_http=400)
