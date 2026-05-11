# -*- coding: utf-8 -*-
"""
Pytest 公共 Fixtures —— 链居房屋租赁系统 API 测试框架
----------------------------------------------------------
提供 Flask 测试客户端、JWT 认证、数据清理等基础设施。
"""

import pytest
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app as flask_app
from exts.db import db as _db


# ══════════════════════════════════════════════════════════════
#  测试用常量
# ══════════════════════════════════════════════════════════════

TEST_PHONE = "19900000001"
TEST_PASSWORD = "Test@123456"
TEST_EMAIL = "autotest_user@test.com"
TEST_NAME = "auto_test_user"

# 动态生成唯一后缀，避免并行测试时的数据冲突
_UNIQUE_SUFFIX = datetime.now().strftime("%m%d%H%M%S")


# ══════════════════════════════════════════════════════════════
#  Pytest 钩子 —— 中文报告输出
# ══════════════════════════════════════════════════════════════

def pytest_report_header(config):
    """测试报告头部"""
    return [
        f"链居房屋租赁系统 - API 自动化测试",
        f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"测试用户: {TEST_PHONE}",
    ]


def pytest_collection_modifyitems(config, items):
    """为每个测试项附加中文描述，在 verbose 模式下更友好"""
    for item in items:
        # 从 test docstring 的第一行提取中文描述
        doc = item.function.__doc__
        if doc:
            first_line = doc.strip().split("\n")[0].strip()
            if any('一' <= c <= '鿿' for c in first_line):
                item._nodeid = f"{item.nodeid}  # {first_line}"


def pytest_runtest_call(item):
    """测试执行前打印中文描述"""
    doc = item.function.__doc__
    if doc:
        first_line = doc.strip().split("\n")[0].strip()
        if any('一' <= c <= '鿿' for c in first_line):
            print(f"\n  >> {first_line}")


# ══════════════════════════════════════════════════════════════
#  Flask App & Client
# ══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def app():
    """创建测试用 Flask 应用（session 级别，整个测试会话复用）"""
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    return flask_app


@pytest.fixture(scope="session")
def client(app):
    """Flask 测试客户端 —— 所有 API 测试的唯一入口"""
    return app.test_client()


# ══════════════════════════════════════════════════════════════
#  JWT 认证 Fixtures
# ══════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def _test_user_id(app, client):
    """
    确保测试用户存在，返回其 user_id。
    先尝试注册（忽略已存在的错误），再登录获取 token。
    """
    with app.app_context():
        client.post("/user/register", data={
            "phone": TEST_PHONE,
            "password": TEST_PASSWORD,
            "email": TEST_EMAIL,
        })

        res = client.post("/user/login", data={
            "phone": TEST_PHONE,
            "password": TEST_PASSWORD,
        })
        body = res.get_json()
        if body is None:
            pytest.fail(f"无法登录测试用户 —— 响应非 JSON: {res.status_code}")
        if not body.get("success"):
            pytest.fail(f"无法登录测试用户: {body.get('message')}")

        token = body["data"]["token"]

        res2 = client.get("/user/userinfo", headers={
            "Authorization": f"Bearer {token}"
        })
        body2 = res2.get_json()
        return body2["data"]["id"]


@pytest.fixture(scope="session")
def auth_token(app, client, _test_user_id):
    """JWT Token（session 级别，24小时有效，覆盖整个测试会话）"""
    res = client.post("/user/login", data={
        "phone": TEST_PHONE,
        "password": TEST_PASSWORD,
    })
    return res.get_json()["data"]["token"]


@pytest.fixture
def auth_headers(auth_token):
    """HTTP 请求头 —— 含 JWT Bearer Token（JSON 请求用）"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}",
    }


@pytest.fixture
def invalid_auth_headers():
    """HTTP 请求头 —— 含无效 Token（测试鉴权失败场景）"""
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer invalid_token_string_12345",
    }


@pytest.fixture
def expired_token(app, client):
    """生成一个已过期的 Token（用于测试 Token 过期处理）"""
    import jwt as pyjwt
    from datetime import timedelta
    payload = {
        'user_id': 1,
        'phone': TEST_PHONE,
        'type': 1,
        'exp': datetime.utcnow() - timedelta(hours=1),  # 1小时前过期
    }
    return pyjwt.encode(payload, flask_app.config['SECRET_KEY'], algorithm="HS256")


# ══════════════════════════════════════════════════════════════
#  数据库事务保护
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def db_session(app):
    """在事务中执行测试，结束后自动回滚，不污染数据库"""
    connection = _db.engine.connect()
    transaction = connection.begin()
    yield _db.session
    _db.session.close()
    transaction.rollback()
    connection.close()


# ══════════════════════════════════════════════════════════════
#  中文断言工具函数
# ══════════════════════════════════════════════════════════════

def assert_success(res, expected_http=None):
    """
    断言 API 返回成功响应。
    返回响应体 dict，供后续断言使用。
    """
    body = res.get_json()
    assert body is not None, (
        f"响应体不是 JSON 格式\n"
        f"  HTTP 状态码: {res.status_code}\n"
        f"  原始响应前200字符: {res.data[:200]}"
    )
    assert body.get("success") is True, (
        f"预期接口返回成功，但实际返回失败\n"
        f"  HTTP {res.status_code} | code={body.get('code')}\n"
        f"  错误信息: {body.get('message', '未知错误')}"
    )
    if expected_http is not None:
        assert res.status_code == expected_http, (
            f"HTTP 状态码不符合预期\n"
            f"  预期: {expected_http}\n"
            f"  实际: {res.status_code}"
        )
    return body


def assert_error(res, expected_http=None, expected_code=None, expected_msg_keyword=None):
    """
    断言 API 返回错误响应。
    兼容两种响应格式:
      - 标准格式: {"success": false, "code": 400, "message": "..."}
      - 简化格式: {"message": "..."}  (部分接口使用)
    返回响应体 dict，供后续断言使用。
    """
    body = res.get_json()
    assert body is not None, (
        f"响应体不是 JSON 格式\n"
        f"  HTTP 状态码: {res.status_code}\n"
        f"  原始响应前200字符: {res.data[:200]}"
    )

    # 兼容 success 字段缺失的情况（部分接口直接用 jsonify 返回错误）
    success_val = body.get("success")
    if success_val is True:
        raise AssertionError(
            f"预期接口返回失败，但实际返回成功\n"
            f"  HTTP {res.status_code} | code={body.get('code')}\n"
            f"  响应: {body}"
        )

    if expected_http is not None:
        assert res.status_code == expected_http, (
            f"HTTP 状态码不符合预期 | 预期: {expected_http} | 实际: {res.status_code}"
        )
    if expected_code is not None:
        assert body.get("code") == expected_code, (
            f"业务错误码不符合预期 | 预期: {expected_code} | 实际: {body.get('code')}"
        )
    if expected_msg_keyword is not None:
        msg = body.get("message", "")
        assert expected_msg_keyword in msg, (
            f"错误信息不包含关键字 '{expected_msg_keyword}'\n  实际信息: {msg}"
        )
    return body


def assert_http_status(res, status_code):
    """断言 HTTP 状态码"""
    assert res.status_code == status_code, (
        f"HTTP 状态码不符合预期 | 预期: {status_code} | 实际: {res.status_code}"
    )


def assert_has_fields(data, *fields):
    """断言字典包含指定字段"""
    for f in fields:
        assert f in data, f"响应数据缺少字段: '{f}'"


def generate_unique_phone():
    """生成唯一手机号，避免测试数据冲突"""
    import random
    return f"199{random.randint(10000000, 99999999)}"


def generate_unique_email():
    """生成唯一邮箱"""
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}@autotest.com"


def generate_unique_name(prefix="test_user"):
    """生成唯一用户名"""
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:6]}"
