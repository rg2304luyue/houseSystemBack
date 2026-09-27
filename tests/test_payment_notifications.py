"""Offline tests for the trusted Alipay notification state machine."""

import asyncio
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.api.v1 import payments
from app.core.time import utc_now_naive
from fastapi import HTTPException


@pytest.mark.parametrize("payment_status", ["paid", "cancelled", "expired", "refunded", "reconciliation_required", "unknown"])
@pytest.mark.parametrize("trade_no", [None, "LEASE-7-token"])
def test_pay_rejects_non_pending_without_mutation(payment_status, trade_no, monkeypatch):
    """Closed or unknown contracts cannot generate or reuse payment links."""
    current = contract(payment_status)
    monkeypatch.setattr(payments, "_expire_pending", lambda db: None)
    current.payment_trade_no = trade_no
    db = MagicMock()
    db.query.return_value = query_result(current)
    with pytest.raises(HTTPException) as error:
        payments.pay(payments.PayRequest(contract_id=7), db, SimpleNamespace(id=3))
    assert error.value.status_code == 409
    assert current.payment_status == payment_status
    assert current.payment_trade_no == trade_no
    db.commit.assert_not_called()


@pytest.mark.parametrize("amount", ["bad", "NaN", "Infinity", "0", "-1", "1.001"])
def test_invalid_amount_does_not_create_trade_number(amount, monkeypatch):
    """Invalid contract amounts must not leave a persisted payment attempt."""
    current = contract()
    monkeypatch.setattr(payments, "_expire_pending", lambda db: None)
    current.rentValue = amount
    current.payment_trade_no = None
    db = MagicMock()
    db.query.return_value = query_result(current)
    with pytest.raises(HTTPException):
        payments.pay(payments.PayRequest(contract_id=7), db, SimpleNamespace(id=3))
    assert current.payment_trade_no is None
    db.commit.assert_not_called()


class FormRequest:
    """Provide an asynchronous form payload without an HTTP server."""

    def __init__(self, payload: dict[str, str]):
        self.payload = payload

    async def form(self):
        """Return a copy because the route removes signature fields."""
        return dict(self.payload)


def callback_payload(**overrides: str) -> dict[str, str]:
    """Build a valid terminal Alipay notification payload."""
    payload = {
        "sign": "signed",
        "sign_type": "RSA2",
        "app_id": "app-1",
        "seller_id": "seller-1",
        "out_trade_no": "LEASE-7-token",
        "trade_no": "ALI-9001",
        "trade_status": "TRADE_SUCCESS",
        "total_amount": "1500.00",
    }
    payload.update(overrides)
    return payload


def contract(payment_status: str = "pending"):
    """Build the contract fields consumed by notification handling."""
    return SimpleNamespace(
        id=7,
        payment_status=payment_status,
        payment_trade_no="LEASE-7-token",
        rentValue="1500.00",
        tenantId=3,
        landlordId=4,
        tenantName="tenant",
        landlordName="landlord",
        houseId=8,
        paid_at=None,
        expires_at=utc_now_naive() + timedelta(minutes=20),
        currentDate=utc_now_naive(),
        payment_notified_at=None,
        payment_notify_trade_no=None,
        payment_notify_amount=None,
        reconciliation_reason=None,
    )


@pytest.fixture
def trusted_callback(monkeypatch):
    """Configure merchant identity and an in-memory successful verifier."""
    monkeypatch.setattr(payments.settings, "ALIPAY_APP_ID", "app-1")
    monkeypatch.setattr(payments.settings, "ALIPAY_SELLER_ID", "seller-1")
    verifier = SimpleNamespace(verify=lambda data, signature: signature == "signed")
    monkeypatch.setattr(payments, "_get_alipay_client", lambda: verifier)
    monkeypatch.setattr(payments, "invalidate_house_caches", lambda _house_id: None)


def query_result(value):
    """Return a query mock supporting the route's filter/lock chain."""
    query = MagicMock()
    query.filter.return_value.with_for_update.return_value.first.return_value = value
    query.filter.return_value.first.return_value = value
    return query


def test_success_notification_marks_paid_and_creates_one_rental(trusted_callback):
    """A trusted pending payment creates its rental exactly once."""
    current = contract()
    db = MagicMock()
    db.query.side_effect = [query_result(current), query_result(None)]

    result = asyncio.run(payments.alipay_notify(FormRequest(callback_payload()), db))

    assert result == "success"
    assert current.payment_status == "paid"
    assert current.payment_notify_trade_no == "ALI-9001"
    assert current.payment_notify_amount == Decimal("1500.00")
    assert current.paid_at is not None
    rental = db.add.call_args.args[0]
    assert rental.contract_id == current.id
    assert rental.source == "payment"
    db.commit.assert_called_once()


def test_repeated_paid_notification_is_idempotent(trusted_callback):
    """A repeated trusted callback acknowledges without another write."""
    current = contract("paid")
    db = MagicMock()
    db.query.return_value = query_result(current)

    result = asyncio.run(payments.alipay_notify(FormRequest(callback_payload()), db))

    assert result == "success"
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_repeated_notification_after_refund_is_acknowledged(trusted_callback):
    """A completed refund is terminal and must not trigger provider retries."""

    current = contract("refunded")
    db = MagicMock()
    db.query.return_value = query_result(current)

    result = asyncio.run(payments.alipay_notify(FormRequest(callback_payload()), db))

    assert result == "success"
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_amount_mismatch_is_rejected_without_state_change(trusted_callback):
    """A signed callback with the wrong amount is not accepted."""
    current = contract()
    db = MagicMock()
    db.query.return_value = query_result(current)

    result = asyncio.run(
        payments.alipay_notify(FormRequest(callback_payload(total_amount="1499.99")), db)
    )

    assert result == "failure"
    assert current.payment_status == "pending"
    db.commit.assert_not_called()


@pytest.mark.parametrize("closed_status", ["expired", "cancelled"])
def test_late_success_requires_reconciliation_without_rental(
    trusted_callback, closed_status
):
    """Money received after closure is recorded but never creates occupancy."""
    current = contract(closed_status)
    db = MagicMock()
    db.query.return_value = query_result(current)

    result = asyncio.run(payments.alipay_notify(FormRequest(callback_payload()), db))

    assert result == "success"
    assert current.payment_status == "reconciliation_required"
    assert current.payment_notify_trade_no == "ALI-9001"
    assert current.payment_notify_amount == Decimal("1500.00")
    assert current.reconciliation_reason == "payment_success_after_contract_closed"
    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_unsupported_signature_type_is_rejected_before_verification(
    trusted_callback, monkeypatch
):
    """Unexpected signature algorithms never reach merchant verification."""
    verifier = MagicMock()
    monkeypatch.setattr(payments, "_get_alipay_client", lambda: verifier)
    db = MagicMock()

    result = asyncio.run(
        payments.alipay_notify(FormRequest(callback_payload(sign_type="MD5")), db)
    )

    assert result == "failure"
    verifier.verify.assert_not_called()
    db.query.assert_not_called()


def test_admin_can_record_external_refund_for_reconciliation():
    """A reviewed external refund closes the state with an audit trail."""

    current = contract("reconciliation_required")
    current.to_dict = lambda: {"id": current.id, "payment_status": current.payment_status}
    db = MagicMock()
    db.query.return_value = query_result(current)
    admin = SimpleNamespace(id=99)

    response = payments.resolve_payment_reconciliation(
        current.id,
        payments.ReconciliationRequest(
            action="record_refund",
            note="支付宝后台退款单已核对完成",
        ),
        db=db,
        admin=admin,
    )

    assert response.message == "支付对账已处理"
    assert current.payment_status == "refunded"
    assert current.reconciled_by == admin.id
    assert current.reconciliation_resolution == "refunded"
    assert current.reconciled_at is not None
    db.commit.assert_called_once()


def test_admin_accepts_reconciled_payment_only_for_still_available_house(monkeypatch):
    """Accepting a late payment rechecks ownership and occupancy before rental creation."""

    current = contract("reconciliation_required")
    current.endDate = utc_now_naive() + timedelta(days=30)
    current.to_dict = lambda: {"id": current.id, "payment_status": current.payment_status}
    house = SimpleNamespace(
        id=current.houseId,
        available=1,
        ownership_status="verified",
        landlord_id=current.landlordId,
    )
    db = MagicMock()
    db.query.side_effect = [query_result(current), query_result(house)]
    ensure_rental = MagicMock()
    monkeypatch.setattr(payments, "house_has_active_occupancy", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(payments, "_ensure_rental", ensure_rental)

    payments.resolve_payment_reconciliation(
        current.id,
        payments.ReconciliationRequest(
            action="accept_payment",
            note="确认房源仍可履约并接受该笔支付",
        ),
        db=db,
        admin=SimpleNamespace(id=99),
    )

    assert current.payment_status == "paid"
    assert current.reconciliation_resolution == "accepted"
    assert house.available == 1
    ensure_rental.assert_called_once_with(db, current)
    db.commit.assert_called_once()
