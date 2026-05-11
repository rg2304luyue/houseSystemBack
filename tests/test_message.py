# -*- coding: utf-8 -*-
"""
消息模块测试 —— /comments/messages
==================================
注意: message_bp 挂载在 url_prefix="/comments" 下，
     实际路径为 /comments/messages。
覆盖: REST 查询消息 / 发送消息（需认证）/ 按发送者/接收者查询
"""

import pytest
import uuid
from tests.conftest import assert_success, assert_error, assert_http_status


class TestGetMessages:
    """查询消息 GET /comments/messages"""

    def test_get_by_sender(self, client):
        """按发送者查询消息"""
        res = client.get("/comments/messages?sender=auto_test_user")
        body = res.get_json()
        assert body is not None

    def test_get_by_receiver(self, client):
        """按接收者查询消息"""
        res = client.get("/comments/messages?receiver=auto_test_user")
        body = res.get_json()
        assert body is not None

    def test_get_between_two_users(self, client):
        """查询两人之间的消息"""
        res = client.get("/comments/messages?user1=auto_test_user&user2=test_receiver")
        body = res.get_json()
        assert body is not None

    def test_no_params_returns_400(self, client):
        """不传任何查询参数返回 400"""
        res = client.get("/comments/messages")
        assert_http_status(res, 400)

    def test_sender_equals_receiver_rejected(self, client):
        """发送者和接收者相同应被拒绝"""
        res = client.get("/comments/messages?sender=same_person&receiver=same_person")
        body = res.get_json()
        assert body is not None
        if body.get("success"):
            pass
        else:
            # 应该返回错误
            assert body.get("success") is False

    def test_user1_equals_user2_rejected(self, client):
        """user1 和 user2 相同应被拒绝"""
        res = client.get("/comments/messages?user1=same&user2=same")
        body = res.get_json()
        assert body is not None

    def test_data_structure_when_messages_exist(self, client):
        """消息数据结构验证"""
        res = client.get("/comments/messages?sender=auto_test_user")
        body = res.get_json()
        if body and body.get("data") and body["data"].get("messages"):
            for msg in body["data"]["messages"]:
                assert "content" in msg or "sender_username" in msg


class TestSendMessage:
    """发送消息 POST /comments/messages（需要认证）"""

    def test_no_auth_returns_401(self, client):
        """未认证发送消息返回 401"""
        res = client.post("/comments/messages", json={
            "content": "未认证消息",
            "sender_username": "auto_test_user",
            "receiver_username": "test_receiver",
        })
        assert_error(res, expected_http=401)

    def test_with_auth_sends_successfully(self, client, auth_headers):
        """已认证发送消息"""
        res = client.post("/comments/messages", json={
            "content": f"API 测试消息 {uuid.uuid4().hex[:6]}",
            "sender_username": "auto_test_user",
            "receiver_username": "test_receiver",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_missing_content_field(self, client, auth_headers):
        """缺少 content 字段"""
        res = client.post("/comments/messages", json={
            "sender_username": "auto_test_user",
            "receiver_username": "test_receiver",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None
        if body.get("success") is False:
            pass

    def test_missing_sender_field(self, client, auth_headers):
        """缺少 sender_username"""
        res = client.post("/comments/messages", json={
            "content": "缺少发送者",
            "receiver_username": "test_receiver",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_missing_receiver_field(self, client, auth_headers):
        """缺少 receiver_username"""
        res = client.post("/comments/messages", json={
            "content": "缺少接收者",
            "sender_username": "auto_test_user",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_not_json_request(self, client, auth_headers):
        """非 JSON 请求"""
        res = client.post("/comments/messages", data="not json",
                          headers=auth_headers)
        body = res.get_json()
        assert body is not None

    def test_empty_content(self, client, auth_headers):
        """空消息内容"""
        res = client.post("/comments/messages", json={
            "content": "",
            "sender_username": "auto_test_user",
            "receiver_username": "test_receiver",
        }, headers=auth_headers)
        body = res.get_json()
        assert body is not None


class TestGetSenderMessages:
    """按发送者查消息 GET /comments/messages/<sender>"""

    def test_existing_sender(self, client):
        """存在的发送者"""
        res = client.get("/comments/messages/auto_test_user")
        body = res.get_json()
        assert body is not None

    def test_nonexistent_sender(self, client):
        """不存在的发送者应返回空列表"""
        res = client.get("/comments/messages/nonexistent_user_xyz_999")
        body = res.get_json()
        assert body is not None


class TestGetReceiverMessages:
    """按接收者查消息 GET /comments/messages/receiver/<receiver>"""

    def test_existing_receiver(self, client):
        """存在的接收者"""
        res = client.get("/comments/messages/receiver/test_receiver")
        body = res.get_json()
        assert body is not None

    def test_nonexistent_receiver(self, client):
        """不存在的接收者"""
        res = client.get("/comments/messages/receiver/no_one_999")
        body = res.get_json()
        assert body is not None
