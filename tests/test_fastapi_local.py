"""Focused unit tests for the FastAPI local-development contract."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi import BackgroundTasks
from langchain_core.messages import AIMessage, ToolMessage

from app.main import app
from app.core.time import utc_now_naive
from app.api.v1.payments import _confirm_paid, _release_reservation, expire_payment
from app.api.v1.users import ChangePasswordRequest, change_password, delete_user
from app.api.v1.houses import HouseDetailRequest, _require_house_owner
from app.api.v1 import auth, chat_ai, messages
from app.services import react_agent
from app.services.react_tools import _house_payload
from app.services.house_agent import (
    find_house_candidates,
    format_house_context,
    merge_house_queries,
    parse_house_constraints,
    parse_rent_type,
)


def test_password_hashing_uses_bcrypt_and_handles_invalid_stored_values():
    from app.core.security import hash_password, verify_password

    hashed = hash_password("correct-password")

    assert hashed.startswith("$2")
    assert verify_password("correct-password", hashed)
    assert not verify_password("wrong-password", hashed)
    assert not verify_password("correct-password", "not-a-password-hash")
    assert not verify_password("correct-password", "")


def test_fastapi_health_and_expected_routes_exist():
    response = TestClient(app).get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    paths = {route.path for route in app.routes}
    assert "/api/v1/users" in paths
    assert "/api/v1/payments/{contract_id}/cancel" in paths
    assert "/api/v1/payments/{contract_id}/expire" in paths
    assert "/api/v1/chat-ai/sessions" in paths
    assert "/api/v1/chat-ai/chat/stream" in paths
    assert "/api/v1/payments/{contract_id}/mock-confirm" in paths
    assert "/api/v1/houses/{house_id}/detail" in paths
    assert "/api/v1/auth/email-code" in paths
    assert "/api/v1/auth/email-code/login" in paths
    assert "/api/v1/messages" in paths
    assert "/api/v1/messages/received" in paths
    assert "/api/v1/chat-ai/runs/{request_id}/cancel" in paths


def test_password_login_accepts_valid_credentials_and_rejects_invalid_ones(monkeypatch):
    user = SimpleNamespace(id=5, phone="13800000000", userType=1)
    user.check_password = lambda password: password == "correct-password"
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = user
    monkeypatch.setattr(auth, "create_access_token", lambda *_args, **_kwargs: "signed-token")

    response = auth.login(
        auth.LoginRequest(phone="13800000000", password="correct-password"), db=db
    )

    assert response.data.token == "signed-token"
    with pytest.raises(HTTPException) as exc:
        auth.login(auth.LoginRequest(phone="13800000000", password="wrong-password"), db=db)
    assert exc.value.status_code == 401


def test_house_agent_parses_constraints_and_refuses_to_invent_results():
    assert parse_house_constraints("推荐岳麓区预算2000元以下的房源") == ("岳麓", 2000)
    assert parse_rent_type("推荐芙蓉区的整租房源") == "整租"
    context = format_house_context([])
    assert "匹配数量=0" in context


def test_house_agent_filters_explicit_rent_type():
    db = MagicMock()
    query = db.query.return_value.filter.return_value
    query.filter.return_value = query
    query.order_by.return_value.limit.return_value.all.return_value = []

    find_house_candidates(db, "推荐芙蓉区的整租房源")

    filters = [call.args[0] for call in query.filter.call_args_list]
    assert any(
        "rent_type" in str(condition) and condition.right.value == "整租"
        for condition in filters
    )
    assert any(
        "region" in str(condition) and condition.right.value == "芙蓉"
        for condition in filters
    )


def test_house_query_merges_history_with_latest_explicit_values():
    query = merge_house_queries([
        "推荐岳麓区预算3000元的合租房源",
        "改成芙蓉区的整租",
    ])

    assert "芙蓉区" in query
    assert "整租" in query
    assert "预算3000元以内" in query
    assert "岳麓" not in query
    assert "合租" not in query
    assert merge_house_queries(["你好"]) == ""


def test_chat_reply_accepts_only_public_agent_final(monkeypatch):
    monkeypatch.setattr(
        react_agent,
        "invoke_react_agent",
        lambda _history: "芙蓉区目前有两套符合条件的整租房源。",
    )

    reply = chat_ai._reply([{"role": "user", "content": "推荐芙蓉区整租房源"}])

    assert reply == "芙蓉区目前有两套符合条件的整租房源。"


@pytest.mark.parametrize(
    "content",
    [
        "好的。（思考：先查询） Action: search_houses_by_criteria",
        "Thought: I should search",
        "<think>先查询数据库</think>",
        "正在为您搜索芙蓉区房源",
        "I called get_house_details for listing 1",
        "get_popular_houses returned three rows",
        "search_rental_knowledge found the answer",
        "get_weather_for_visit returned sunny",
    ],
)
def test_private_ai_protocol_variants_are_detected(content):
    assert chat_ai._contains_private_protocol(content)


def test_chat_reply_rejects_private_agent_final(monkeypatch):
    monkeypatch.setattr(
        react_agent,
        "invoke_react_agent",
        lambda _history: "Thought: search first Action: search_houses_by_criteria",
    )

    with pytest.raises(RuntimeError, match="可安全展示"):
        chat_ai._reply([{"role": "user", "content": "推荐芙蓉区整租房源"}])


def test_agent_house_payload_excludes_private_landlord_fields():
    house = SimpleNamespace(**{
        field: None for field in (
            "id", "title", "region", "block", "community", "area", "direction",
            "rooms", "price", "rent_type", "decoration", "subway", "tag_new",
            "image_url", "publish_time", "page_views", "house_num",
        )
    })
    house.landlord = "private"
    house.landlord_id = 9
    house.phone_num = "13800000000"

    payload = _house_payload(house)

    assert "landlord" not in payload
    assert "landlord_id" not in payload
    assert "phone_num" not in payload


def test_react_stream_exposes_status_and_final_only(monkeypatch):
    class FakeAgent:
        def stream(self, *_args, **_kwargs):
            yield {"model": {"messages": [AIMessage(
                content="PRIVATE_DRAFT",
                tool_calls=[{"name": "search_houses_by_criteria", "args": {"region": "芙蓉"}, "id": "call-1"}],
            )]}}
            yield {"tools": {"messages": [ToolMessage(
                content='{"phone_num":"PRIVATE_RESULT"}',
                tool_call_id="call-1",
            )]}}
            yield {"model": {"messages": [AIMessage(content="公开最终答复")]}}

    monkeypatch.setattr(react_agent, "get_react_agent", lambda: FakeAgent())

    events = list(react_agent.stream_react_agent([
        {"role": "user", "content": "推荐芙蓉区房源"}
    ]))
    serialized = str(events)

    assert [event["type"] for event in events] == ["status", "status", "answer"]
    assert events[-1]["content"] == "公开最终答复"
    assert "PRIVATE_DRAFT" not in serialized
    assert "PRIVATE_RESULT" not in serialized
    assert "search_houses_by_criteria" not in serialized


def test_old_private_protocol_is_hidden_from_history():
    content = "（思考：查询） Action: search_houses_by_criteria"

    public_content = chat_ai._public_history_content(content)

    assert "Action" not in public_content
    assert "search_houses_by_criteria" not in public_content


def test_confirm_paid_creates_rental_once():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    contract = SimpleNamespace(
        id=21,
        payment_status="pending",
        paid_at=None,
        houseId=7,
        tenantId=3,
        landlordId=4,
        tenantName="tenant",
        landlordName="landlord",
    )

    _confirm_paid(db, contract)

    assert contract.payment_status == "paid"
    assert contract.paid_at is not None
    db.add.assert_called_once()
    rental = db.add.call_args.args[0]
    assert rental.contract_id == 21
    assert rental.tenant_id == 3
    assert rental.landlord_id == 4


def test_release_reservation_restores_house():
    house = SimpleNamespace(available=0)
    db = MagicMock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = house
    contract = SimpleNamespace(
        payment_status="pending", houseId=8, tenantName="tenant"
    )

    _release_reservation(db, contract, "cancelled")

    assert contract.payment_status == "cancelled"
    assert house.available == 1


def test_expire_payment_releases_an_overdue_reservation():
    house = SimpleNamespace(available=0)
    contract = SimpleNamespace(
        id=9,
        tenantId=3,
        tenantName="tenant",
        houseId=8,
        payment_status="pending",
        expires_at=utc_now_naive() - timedelta(minutes=1),
        to_dict=lambda: {"id": 9, "payment_status": "expired"},
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.side_effect = [contract, house]

    response = expire_payment(9, db=db, current_user=SimpleNamespace(id=3))

    assert contract.payment_status == "expired"
    assert house.available == 1
    db.commit.assert_called_once()
    assert response.data["payment_status"] == "expired"


def test_admin_cannot_delete_self():
    admin = SimpleNamespace(id=11)
    with pytest.raises(HTTPException) as exc:
        delete_user(11, db=MagicMock(), admin=admin)
    assert exc.value.status_code == 409


def test_password_change_requires_current_password():
    user = MagicMock()
    user.check_password.return_value = False
    with pytest.raises(HTTPException) as exc:
        change_password(
            ChangePasswordRequest(current_password="wrong", password="new-password"),
            db=MagicMock(),
            current_user=user,
        )
    assert exc.value.status_code == 400
    user.set_password.assert_not_called()


def test_house_detail_validates_coordinates_and_photos():
    valid = HouseDetailRequest(
        photos=["/images/room.jpg"],
        facilities={"wifi": True},
        map_coordinates={"lat": 28.2, "lng": 112.9},
    )
    assert valid.facilities["wifi"] is True
    with pytest.raises(ValueError):
        HouseDetailRequest(photos=[], facilities={}, map_coordinates={"lat": 91, "lng": 0})
    with pytest.raises(ValueError):
        HouseDetailRequest(photos=["  "], facilities={}, map_coordinates={"lat": 0, "lng": 0})


def test_only_admin_or_house_owner_can_write_detail():
    house = SimpleNamespace(landlord_id=7)
    _require_house_owner(house, SimpleNamespace(userType=0, name="admin", phone=None))
    _require_house_owner(house, SimpleNamespace(id=7, userType=2, name="renamed", phone=None))
    with pytest.raises(HTTPException) as exc:
        _require_house_owner(house, SimpleNamespace(id=8, userType=2, name="renamed", phone=None))
    assert exc.value.status_code == 403


def test_chat_stream_uses_a_dedicated_database_session(monkeypatch):
    stream_db = MagicMock()
    stream_db.get.return_value = SimpleNamespace(updated_at=None)
    context = MagicMock()
    context.__enter__.return_value = stream_db
    context.__exit__.return_value = False

    monkeypatch.setattr(chat_ai, "SessionLocal", MagicMock(return_value=context))
    monkeypatch.setattr(
        react_agent,
        "stream_react_agent",
        lambda _history: iter([
            {"type": "status", "status": "正在查询相关信息"},
            {"type": "answer", "content": "测试回复"},
        ]),
    )

    events = list(chat_ai._stream_events(42, [{"role": "user", "content": "你好"}]))

    assert any('"label": "正在思考中"' in event for event in events)
    assert any('"label": "正在查询相关信息"' in event for event in events)
    assert any('"type": "chunk"' in event and "测试回复" in event for event in events)
    assert '"session_id": 42' in events[-1]
    stream_db.get.assert_called_once_with(chat_ai.ChatSession, 42)
    stream_db.commit.assert_called_once()
    saved_message = stream_db.add.call_args.args[0]
    assert saved_message.session_id == 42


def test_chat_stream_reports_ai_failure_without_opening_database(monkeypatch):
    session_factory = MagicMock()
    monkeypatch.setattr(chat_ai, "SessionLocal", session_factory)
    def fail(_history):
        raise RuntimeError("private provider failure")

    monkeypatch.setattr(react_agent, "stream_react_agent", fail)

    events = list(chat_ai._stream_events(42, [{"role": "user", "content": "你好"}]))

    assert '"type": "error"' in events[-1]
    assert "private provider failure" not in events[-1]
    session_factory.assert_not_called()


def test_chat_stream_returns_sanitized_quota_message(monkeypatch):
    from app.services.react_agent import AgentPublicError

    def fail(_history):
        raise AgentPublicError("DeepSeek 账户余额不足，请充值后重试。")

    monkeypatch.setattr(react_agent, "stream_react_agent", fail)
    events = list(chat_ai._stream_events(42, [{"role": "user", "content": "你好"}]))
    serialized = "".join(events)

    assert "DeepSeek 账户余额不足" in serialized
    assert "AllocationQuota" not in serialized


def test_chat_stream_preserves_cancelled_state_when_agent_fails(monkeypatch):
    monkeypatch.setattr(chat_ai, "_run_cancelled", lambda _request_id: True)
    set_state = MagicMock()
    monkeypatch.setattr(chat_ai, "_set_run_state", set_state)

    def fail(_history):
        raise RuntimeError("provider failed after cancellation")

    monkeypatch.setattr(react_agent, "stream_react_agent", fail)

    events = list(chat_ai._stream_events(
        42,
        [{"role": "user", "content": "你好"}],
        "12345678-1234-5678-1234-567812345678",
    ))

    assert '"type": "cancelled"' in events[-1]
    assert not any('"type": "error"' in event for event in events)
    set_state.assert_called_once_with(
        "12345678-1234-5678-1234-567812345678",
        "cancelled",
        error_code="CANCELLED",
    )


def test_cancel_agent_run_marks_owned_running_request_cancelled():
    run = SimpleNamespace(
        user_id=7,
        status="running",
        cancel_requested=False,
        error_code=None,
        updated_at=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = run

    response = chat_ai.cancel_agent_run(
        UUID("12345678-1234-5678-1234-567812345678"),
        db=db,
        current_user=SimpleNamespace(id=7),
    )

    assert run.cancel_requested is True
    assert run.status == "cancelled"
    assert run.error_code == "CANCELLED"
    assert response.data == {"status": "cancelled"}
    db.commit.assert_called_once()


def test_cancel_agent_run_hides_another_users_request():
    db = MagicMock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = (
        SimpleNamespace(user_id=8)
    )

    with pytest.raises(HTTPException) as exc:
        chat_ai.cancel_agent_run(
            UUID("12345678-1234-5678-1234-567812345678"),
            db=db,
            current_user=SimpleNamespace(id=7),
        )

    assert exc.value.status_code == 404


def test_send_email_login_code_is_rate_limited_and_queued(monkeypatch):
    user = SimpleNamespace(email="user@example.com")
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = user
    redis_client = MagicMock()
    redis_client.set.return_value = True
    redis_client.pipeline.return_value.execute.return_value = [1, True]
    monkeypatch.setattr(auth, "is_redis_available", lambda: True)
    monkeypatch.setattr(auth, "get_redis", lambda: redis_client)
    monkeypatch.setattr(auth.settings, "QQ_SMTP_EMAIL", "sender@example.com")
    monkeypatch.setattr(auth.settings, "QQ_SMTP_AUTH_CODE", "smtp-secret")
    monkeypatch.setattr(auth.secrets, "randbelow", lambda _limit: 777777)
    tasks = BackgroundTasks()

    response = auth.send_email_code(
        auth.EmailCodeRequest(email=" USER@example.com "), tasks, db=db
    )

    assert response.success is True
    redis_client.set.assert_any_call(
        "email_login_last_send:user@example.com", "1", ex=60, nx=True
    )
    redis_client.set.assert_any_call(
        "email_login_code:user@example.com", "777777", ex=300
    )
    assert len(tasks.tasks) == 1


def test_email_code_login_consumes_code_and_issues_token(monkeypatch):
    user = SimpleNamespace(id=5, phone="13800000000", email="user@example.com", userType=1)
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = user
    redis_client = MagicMock()
    redis_client.eval.return_value = 1
    monkeypatch.setattr(auth, "is_redis_available", lambda: True)
    monkeypatch.setattr(auth, "get_redis", lambda: redis_client)
    create_token = MagicMock(return_value="signed-token")
    monkeypatch.setattr(auth, "create_access_token", create_token)

    response = auth.email_code_login(
        auth.EmailCodeLoginRequest(email="user@example.com", code="123456"), db=db
    )

    assert response.data.token == "signed-token"
    redis_client.eval.assert_called_once_with(
        auth._CONSUME_CODE_SCRIPT, 1, "email_login_code:user@example.com", "123456"
    )
    create_token.assert_called_once_with(
        5, phone="13800000000", email="user@example.com", user_type=1
    )


def test_send_message_uses_authenticated_sender():
    sender = SimpleNamespace(id=3, name="alice")
    receiver = SimpleNamespace(id=4, name="bob")
    channel = SimpleNamespace(channel_id=9)
    receiver_query = MagicMock()
    receiver_query.filter_by.return_value.all.return_value = [receiver]
    channel_query = MagicMock()
    channel_query.filter.return_value.first.return_value = channel
    db = MagicMock()
    db.query.side_effect = [receiver_query, channel_query]
    db.refresh.side_effect = lambda message: setattr(message, "message_id", 41)

    response = messages.send_message(
        messages.MessageCreate(receiver_username="bob", content=" hello "),
        db=db,
        current_user=sender,
    )

    saved = db.add.call_args.args[0]
    assert saved.sender_username == "alice"
    assert saved.receiver_username == "bob"
    assert saved.sender_id == 3
    assert saved.receiver_id == 4
    assert saved.content == "hello"
    assert saved.channel_id == 9
    assert response.data["message_id"] == 41
    db.commit.assert_called_once()


def test_received_messages_filters_by_authenticated_user():
    record = SimpleNamespace(to_dict=lambda: {"message_id": 1})
    query = MagicMock()
    query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [record]
    db = MagicMock()
    db.query.return_value = query

    response = messages.received_messages(
        limit=10, db=db, current_user=SimpleNamespace(id=3, name="alice")
    )

    assert response.data == [{"message_id": 1}]
    query.filter.assert_called_once()
