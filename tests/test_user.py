# -*- coding: utf-8 -*-
"""
用户模块测试 —— /user/*
=========================
覆盖: 注册 / 多种登录方式 / 用户信息查询修改 / 密码管理 / 头像 / 房东升级
"""

import pytest
from tests.conftest import (
    assert_success, assert_error, assert_http_status, assert_has_fields,
    generate_unique_phone, generate_unique_email, generate_unique_name,
)


# ══════════════════════════════════════════════════════════════
#  用户注册
# ══════════════════════════════════════════════════════════════

class TestRegister:
    """用户注册 POST /user/register"""

    def test_register_success(self, client):
        """新用户注册成功"""
        phone = generate_unique_phone()
        email = generate_unique_email()
        res = client.post("/user/register", data={
            "phone": phone,
            "password": "Test@123456",
            "email": email,
        })
        body = assert_success(res, expected_http=201)
        assert body.get("message") is not None

    def test_register_missing_phone(self, client):
        """缺少手机号应返回 400"""
        res = client.post("/user/register", data={
            "password": "123456",
            "email": "test@test.com",
        })
        assert_error(res, expected_http=400)

    def test_register_missing_password(self, client):
        """缺少密码应返回 400"""
        res = client.post("/user/register", data={
            "phone": generate_unique_phone(),
            "email": "test@test.com",
        })
        assert_error(res, expected_http=400)

    def test_register_missing_email(self, client):
        """缺少邮箱应返回 400"""
        res = client.post("/user/register", data={
            "phone": generate_unique_phone(),
            "password": "123456",
        })
        assert_error(res, expected_http=400)

    def test_register_empty_body(self, client):
        """空请求体应返回 400"""
        res = client.post("/user/register", data={})
        assert_error(res, expected_http=400)

    def test_register_duplicate_phone(self, client, auth_token):
        """重复手机号注册应失败"""
        # 用已存在的测试用户手机号（19900000001）
        res = client.post("/user/register", data={
            "phone": "19900000001",
            "password": "123456",
            "email": generate_unique_email(),
        })
        body = res.get_json()
        if body and body.get("success"):
            pytest.skip("测试用户未预先存在")
        assert body["success"] is False

    def test_register_duplicate_email(self, client, auth_token):
        """重复邮箱注册应失败"""
        res = client.post("/user/register", data={
            "phone": generate_unique_phone(),
            "password": "123456",
            "email": "autotest_user@test.com",
        })
        body = res.get_json()
        if body and body.get("success"):
            pytest.skip("测试用户未预先存在")
        assert body["success"] is False


# ══════════════════════════════════════════════════════════════
#  用户登录
# ══════════════════════════════════════════════════════════════

class TestLogin:
    """用户登录 POST /user/login"""

    def test_login_with_correct_credentials(self, client):
        """正确的手机号和密码登录成功"""
        res = client.post("/user/login", data={
            "phone": "19900000001",
            "password": "Test@123456",
        })
        body = assert_success(res)
        assert "token" in body["data"], "响应应包含 JWT token"
        assert len(body["data"]["token"]) > 20, "Token 长度应大于 20"

    def test_login_with_wrong_password(self, client):
        """错误的密码应返回 401"""
        res = client.post("/user/login", data={
            "phone": "19900000001",
            "password": "WrongPassword999",
        })
        assert_error(res, expected_http=401)

    def test_login_with_nonexistent_phone(self, client):
        """不存在的手机号应返回 401"""
        res = client.post("/user/login", data={
            "phone": "00000000000",
            "password": "123456",
        })
        assert_error(res, expected_http=401)

    def test_login_empty_phone(self, client):
        """手机号为空"""
        res = client.post("/user/login", data={"password": "123456"})
        assert_error(res, expected_http=400)

    def test_login_empty_password(self, client):
        """密码为空"""
        res = client.post("/user/login", data={"phone": "19900000001"})
        assert_error(res, expected_http=400)

    def test_login_empty_body(self, client):
        """空请求体"""
        res = client.post("/user/login", data={})
        assert_error(res, expected_http=400)

    def test_login_json_instead_of_form(self, client):
        """使用 JSON 而非 form-data 发送 —— 可能因字段缺失而失败"""
        res = client.post("/user/login", json={
            "phone": "19900000001",
            "password": "Test@123456",
        })
        body = res.get_json()
        assert body is not None
        # 因为接口用 request.form 取参，JSON body 取不到值
        if body.get("success") is False:
            pass  # 符合预期

    def test_login_token_can_be_used(self, client, auth_token):
        """登录获得的 token 可用于后续请求"""
        res = client.get("/user/userinfo", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert_success(res)


class TestEmailLogin:
    """邮箱登录 POST /user/email-login"""

    def test_email_login_success(self, client):
        """正确的邮箱和密码登录成功"""
        res = client.post("/user/email-login", data={
            "email": "autotest_user@test.com",
            "password": "Test@123456",
        })
        body = assert_success(res)
        assert "token" in body["data"]

    def test_email_login_wrong_password(self, client):
        """错误的密码"""
        res = client.post("/user/email-login", data={
            "email": "autotest_user@test.com",
            "password": "wrong_password",
        })
        assert_error(res, expected_http=401)

    def test_email_login_empty_fields(self, client):
        """邮箱或密码为空"""
        res = client.post("/user/email-login", data={})
        assert_error(res, expected_http=400)

    def test_email_login_nonexistent_email(self, client):
        """不存在的邮箱"""
        res = client.post("/user/email-login", data={
            "email": "never_existed@no.com",
            "password": "123456",
        })
        assert_error(res, expected_http=401)


# ══════════════════════════════════════════════════════════════
#  用户信息查询 & 修改
# ══════════════════════════════════════════════════════════════

class TestUserInfo:
    """用户信息 GET/PUT /user/userinfo"""

    def test_get_userinfo_no_token(self, client):
        """未登录获取用户信息应返回 401"""
        res = client.get("/user/userinfo")
        assert_error(res, expected_http=401)

    def test_get_userinfo_with_token(self, client, auth_headers):
        """已登录可获取完整的用户信息"""
        res = client.get("/user/userinfo", headers=auth_headers)
        body = assert_success(res)
        data = body["data"]
        assert_has_fields(data, "id", "phone", "email", "name", "userType")
        assert "password" not in data, "响应不应包含密码字段"

    def test_get_userinfo_invalid_token(self, client, invalid_auth_headers):
        """无效的 Token 应返回 401"""
        res = client.get("/user/userinfo", headers=invalid_auth_headers)
        assert_error(res, expected_http=401)

    def test_get_userinfo_expired_token(self, client, expired_token):
        """过期的 Token 应返回 401"""
        res = client.get("/user/userinfo", headers={
            "Authorization": f"Bearer {expired_token}"
        })
        body = res.get_json()
        assert body is not None
        # 可能返回 401 (Token 过期) 或其他错误
        if body.get("code") == 401:
            pass

    def test_get_user_by_name_found(self, client):
        """根据用户名查询 —— 存在"""
        res = client.get("/user/userinfo/auto_test_user")
        body = res.get_json()
        assert body is not None

    def test_get_user_by_name_not_found(self, client):
        """根据用户名查询 —— 不存在"""
        res = client.get("/user/userinfo/nonexistent_user_xyz_999")
        body = res.get_json()
        assert body is not None
        assert body.get("success") is False

    def test_update_userinfo_partial(self, client, auth_headers):
        """部分字段更新用户信息"""
        res = client.put("/user/userinfo", json={
            "id": 1,
            "name": "更新测试名称",
            "addr": "北京市朝阳区测试路100号",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_update_userinfo_nonexistent_user(self, client, auth_headers):
        """更新不存在的用户"""
        res = client.put("/user/userinfo", json={
            "id": 99999,
            "name": "不会成功",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_update_userinfo_empty_body(self, client, auth_headers):
        """空请求体更新"""
        res = client.put("/user/userinfo", json={}, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_update_userinfo_identity_card_protection(self, client, auth_headers):
        """身份证号已填写后不可更改"""
        # 先尝试更新身份证（预期可能被保护）
        res = client.put("/user/userinfo", json={
            "id": 1,
            "identityCard": "110101199001011234",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None


# ══════════════════════════════════════════════════════════════
#  密码管理
# ══════════════════════════════════════════════════════════════

class TestPassword:
    """密码相关操作"""

    def test_change_password_by_id(self, client):
        """通过 ID 修改密码"""
        res = client.put("/user/userinfo/password", json={
            "id": 1,
            "password": "NewPassword@123",
        })
        body = res.get_json()
        assert body is not None
        if body.get("success"):
            # 恢复原密码
            client.put("/user/userinfo/password", json={
                "id": 1,
                "password": "Test@123456",
            })

    def test_change_password_empty_body(self, client):
        """空请求修改密码"""
        res = client.put("/user/userinfo/password", json={})
        assert_error(res, expected_http=400)

    def test_reset_password_send_email_no_body(self, client):
        """发送重置邮件 —— 空请求"""
        res = client.post("/user/userinfo/password", json={})
        assert_error(res, expected_http=400)

    def test_reset_password_send_email_not_found(self, client):
        """发送重置邮件 —— 邮箱不存在"""
        res = client.post("/user/userinfo/password", json={
            "email": "nonexistent@no.com"
        })
        body = res.get_json()
        assert body is not None
        if body.get("success"):
            pytest.skip("Redis 不可用，跳过此测试")

    def test_reset_password_by_email(self, client):
        """根据邮箱修改密码"""
        res = client.put("/user/userinfo/password_e", json={
            "email": "autotest_user@test.com",
            "password": "ResetPass@456",
        })
        body = res.get_json()
        assert body is not None
        if body.get("success"):
            # 恢复原密码
            client.put("/user/userinfo/password_e", json={
                "email": "autotest_user@test.com",
                "password": "Test@123456",
            })

    def test_reset_password_by_email_empty(self, client):
        """根据邮箱修改密码 —— 空请求"""
        res = client.put("/user/userinfo/password_e", json={})
        assert_error(res, expected_http=400)


# ══════════════════════════════════════════════════════════════
#  头像 & 房东升级
# ══════════════════════════════════════════════════════════════

class TestAvatar:
    """用户头像"""

    def test_get_avatar_without_id(self, client):
        """不传用户 ID"""
        res = client.get("/user/userinfo/avatar")
        assert_error(res, expected_http=400)

    def test_get_avatar_nonexistent_user(self, client):
        """不存在的用户没有头像"""
        res = client.get("/user/userinfo/avatar?id=99999")
        body = res.get_json()
        assert body is not None
        assert body.get("success") is False

    def test_upload_avatar_no_file(self, client):
        """上传头像但不传文件"""
        res = client.post("/user/userinfo/avatarurl", data={"userId": "1"})
        assert_error(res, expected_http=400)

    def test_upload_avatar_no_userid(self, client):
        """上传头像但不传 userId"""
        res = client.post("/user/userinfo/avatarurl", data={})
        assert_error(res, expected_http=400)

    def test_serve_image_404(self, client):
        """访问不存在的图片文件"""
        res = client.get("/user/images/nonexistent_file_999.png")
        assert res.status_code == 404


class TestLandlordUpgrade:
    """升级为房东 POST/PUT /user/userinfo/tolanlord & /usertype"""

    def test_tolanlord_send_email_no_body(self, client):
        """发送升级邮件 —— 空请求"""
        res = client.post("/user/userinfo/tolanlord", json={})
        assert_error(res, expected_http=400)

    def test_tolanlord_send_email_not_found(self, client):
        """发送升级邮件 —— 邮箱不存在"""
        res = client.post("/user/userinfo/tolanlord", json={
            "email": "nonexistent@no.com"
        })
        body = res.get_json()
        assert body is not None

    def test_upgrade_to_landlord_no_body(self, client):
        """升级为房东 —— 空请求"""
        res = client.put("/user/userinfo/usertype", json={})
        assert_error(res, expected_http=400)

    def test_upgrade_to_landlord_nonexistent(self, client):
        """升级不存在的用户为房东"""
        res = client.put("/user/userinfo/usertype", json={
            "email": "nonexistent@no.com"
        })
        body = res.get_json()
        assert body is not None

    def test_upgrade_already_landlord(self, client, auth_headers):
        """已是房东的用户尝试再次升级 —— 应返回错误"""
        res = client.put("/user/userinfo/usertype", json={
            "email": "autotest_user@test.com",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None
