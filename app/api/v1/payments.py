"""Payment routes: Alipay sandbox payment generation and callback handling.

POST /api/v1/payments/pay
    Generate an Alipay sandbox page-pay URL for a given contract.
    The server generates the out_trade_no and reads the amount from the
    contract record (never from client input).

POST /api/v1/payments/notify
    Handle Alipay's asynchronous payment notification.
    Verifies the signature, validates the amount,
    and updates the contract payment status to 'paid' (idempotent).

Payment state machine (P0.4):
    pending -> paid | cancelled | expired
    - House pre-occupied when contract created (available=0)
    - On paid: confirm rental, mark paid_at
    - Prevent re-payment of already-paid contracts
    - Prevent changing trade_no once set
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Literal
from app.core.time import utc_now_naive

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import get_current_admin, get_current_user
from app.db.session import get_db
from app.models.contract import Contract
from app.models.house import HouseInfo
from app.models.rental import Rental
from app.models.user import UserModel
from app.services.house_cache import invalidate_house_caches
from app.core.config import settings
from app.schemas.common import APIResponse
from app.services.occupancy import (
    expired_pending_condition,
    pending_contract_is_expired,
    pending_deadline,
    house_has_active_occupancy,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payments"])

# ---------------------------------------------------------------------------
# Lazy import AlipayClient (may fail if keys are missing)
# ---------------------------------------------------------------------------

_alipay_client = None


def _get_alipay_client():
    """Lazily initialize and return the shared AlipayClient singleton."""
    global _alipay_client
    if _alipay_client is None:
        try:
            from exts.alipay_client import AlipayClient

            _alipay_client = AlipayClient()
            logger.info("AlipayClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AlipayClient: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="支付服务暂不可用，请稍后重试",
            )
    return _alipay_client


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class PayRequest(BaseModel):
    """Request to initiate a payment for a contract.

    Only contract_id is accepted from the client. The out_trade_no is
    generated server-side and the amount is read from the contract record.
    """

    contract_id: int = Field(..., description="Contract ID to pay for")


class PayResponse(BaseModel):
    """Payment URL response."""

    pay_url: str
    out_trade_no: str


class ReconciliationRequest(BaseModel):
    action: Literal["accept_payment", "record_refund"]
    note: str = Field(..., min_length=3, max_length=500)


def _release_reservation(db: Session, contract: Contract, new_status: str) -> None:
    """Release a pending reservation without touching paid rental history."""
    if contract.payment_status != "pending" or new_status not in {"cancelled", "expired"}:
        raise ValueError("only a pending reservation can be released")
    contract.payment_status = new_status


def _expire_pending(db: Session, now: datetime | None = None) -> None:
    """Expire overdue reservations opportunistically on payment operations."""
    now = now or utc_now_naive()
    overdue = db.query(Contract).filter(
        expired_pending_condition(now),
    ).with_for_update(skip_locked=True).all()
    for contract in overdue:
        if contract.expires_at is None:
            contract.expires_at = pending_deadline(contract) or now
        _release_reservation(db, contract, "expired")
    if overdue:
        try:
            db.commit()
            for contract in overdue:
                invalidate_house_caches(contract.houseId)
        except Exception:
            db.rollback()
            logger.exception("Failed to release expired lease reservations")
            raise


def _ensure_rental(db: Session, contract: Contract) -> None:
    """Create the contract-backed rental exactly once."""

    rental = db.query(Rental).filter(Rental.contract_id == contract.id).first()
    if rental is None:
        db.add(Rental(
            contract_id=contract.id,
            tenant_id=contract.tenantId,
            landlord_id=contract.landlordId,
            tenant_username=contract.tenantName,
            landlord_username=contract.landlordName,
            house_id=contract.houseId,
            currentDate=utc_now_naive(),
            source="payment",
        ))


def _confirm_paid(db: Session, contract: Contract) -> None:
    """Confirm a pending contract exactly once and create its rental record."""
    if contract.payment_status == "paid":
        return
    if contract.payment_status != "pending":
        raise ValueError("contract is no longer payable")
    _ensure_rental(db, contract)
    contract.payment_status = "paid"
    contract.paid_at = utc_now_naive()


# ---------------------------------------------------------------------------
# POST /payments/pay
# ---------------------------------------------------------------------------


@router.post("/payments/pay", response_model=APIResponse[PayResponse])
def pay(
    body: PayRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Generate an Alipay sandbox payment URL for a contract.

    Security guarantees:
    - out_trade_no is generated server-side (UUID-based, unique)
    - Amount is read from contract.rentValue, never from client input
    - Only the contract's tenant can initiate payment
    - Already-paid contracts cannot be re-paid
    - Once a trade_no is set, it cannot be overwritten with a different value
    """
    # ---- 1. Fetch and validate contract ----
    _expire_pending(db)
    contract = (
        db.query(Contract)
        .filter(Contract.id == body.contract_id)
        .with_for_update()
        .first()
    )
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同不存在",
        )

    # ---- 2. Verify the current user is the contract tenant ----
    if contract.tenantId != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该合同的租客，无法支付",
        )

    # ---- 3. Prevent re-payment ----
    if contract.payment_status != "pending":
        detail = {
            "paid": "该合同已完成支付，请勿重复支付",
            "reconciliation_required": "支付结果正在人工对账，请勿重复支付",
            "cancelled": "合同已取消，请重新签约",
            "expired": "合同已过期，请重新签约",
            "refunded": "该合同已退款，无法再次支付",
        }.get(contract.payment_status, "合同状态不允许支付，请重新签约")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=detail
        )
    now = utc_now_naive()
    if contract.payment_status == "pending" and pending_contract_is_expired(contract, now):
        if contract.expires_at is None:
            contract.expires_at = pending_deadline(contract) or now
        _release_reservation(db, contract, "expired")
        db.commit()
        invalidate_house_caches(contract.houseId)
        raise HTTPException(status_code=409, detail="合同已过期，请重新签约")

    try:
        amount = Decimal(str(contract.rentValue))
        if not amount.is_finite() or amount <= 0 or amount != amount.quantize(Decimal("0.01")):
            raise ValueError
        total_amount = float(amount)
    except (ValueError, TypeError, InvalidOperation):
        raise HTTPException(status_code=500, detail="合同金额格式错误")

    # ---- 4. Generate or reuse out_trade_no (prevent changing trade_no) ----
    if contract.payment_trade_no is not None:
        # Trade_no already exists — regenerate the pay URL idempotently
        out_trade_no = contract.payment_trade_no
        logger.info(
            f"Reusing existing trade_no={out_trade_no} for contract_id={contract.id}"
        )
    else:
        # Generate a new server-side out_trade_no
        out_trade_no = f"LEASE-{contract.id}-{uuid.uuid4().hex[:12]}"
        contract.payment_trade_no = out_trade_no
        contract.payment_status = "pending"
        try:
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(
                f"Failed to save trade_no for contract_id={contract.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="支付初始化失败，请稍后重试",
            )

    subject = f"房屋租赁-合同#{contract.id}"

    # ---- 6. Generate Alipay payment URL ----
    try:
        alipay = _get_alipay_client()
        pay_url = alipay.generate_payment_url(
            out_trade_no=out_trade_no,
            total_amount=total_amount,
            subject=subject,
        )
        logger.info(
            f"Payment URL generated: contract_id={contract.id}, "
            f"trade_no={out_trade_no}, amount={total_amount:.2f}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Failed to generate payment URL: contract_id={contract.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成支付链接失败，请稍后重试",
        )

    return APIResponse(
        code=200,
        data=PayResponse(pay_url=pay_url, out_trade_no=out_trade_no),
        message="支付链接生成成功",
    )


# ---------------------------------------------------------------------------
# POST /payments/notify  (Alipay async callback)
# ---------------------------------------------------------------------------


@router.post("/payments/notify", response_class=PlainTextResponse)
async def alipay_notify(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Alipay's asynchronous payment notification.

    This endpoint is called by Alipay's server, NOT by the client browser.
    - Verifies the RSA signature in every environment
    - Validates that the paid amount matches the contract amount
    - Idempotently updates contract.payment_status to 'paid'
    - Returns plain text 'success' or 'failure' as required by Alipay

    IMPORTANT: This endpoint does NOT require JWT authentication because
    it is called by Alipay's server, not the end user.
    """
    # Alipay sends form-urlencoded data
    form_data = await request.form()
    data = dict(form_data)
    signature = data.pop("sign", None)
    sign_type = data.pop("sign_type", None)

    # Alipay's callback signature algorithm is part of the trust boundary.
    # Reject missing or unexpected algorithms before invoking the verifier.
    if str(sign_type or "").upper() not in {"RSA", "RSA2"}:
        logger.warning("Alipay notify rejected unsupported sign_type=%s", sign_type)
        return "failure"

    # ---- 1. Verify signature ----
    try:
        alipay = _get_alipay_client()
        if not alipay.verify(data, signature):
            logger.warning(
                f"Alipay notify signature verification failed: "
                f"out_trade_no={data.get('out_trade_no')}"
            )
            return "failure"
    except HTTPException:
        # The callback protocol requires a raw acknowledgement even when
        # payment configuration is unavailable.
        return "failure"
    except Exception as e:
        logger.exception(f"Alipay notify signature verification error: {e}")
        return "failure"

    out_trade_no = data.get("out_trade_no")
    trade_status = data.get("trade_status")
    total_amount_str = data.get("total_amount")
    seller_id = data.get("seller_id")
    app_id = data.get("app_id")

    # ---- 2. Only process terminal states ----
    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        logger.info(
            f"Alipay notify ignored (non-terminal status): "
            f"out_trade_no={out_trade_no}, status={trade_status}"
        )
        return "success"

    # ---- 3. Validate seller/merchant in every environment ----
    expected_seller = settings.ALIPAY_SELLER_ID
    if not expected_seller or seller_id != expected_seller:
        logger.warning("Alipay notify seller_id is missing or does not match")
        return "failure"
    if not settings.ALIPAY_APP_ID or app_id != settings.ALIPAY_APP_ID:
        logger.warning("Alipay notify app_id is missing or does not match")
        return "failure"

    # ---- 4. Find contract by trade_no ----
    contract = (
        db.query(Contract)
        .filter(Contract.payment_trade_no == out_trade_no)
        .with_for_update()
        .first()
    )

    if contract is None:
        logger.error(
            f"Alipay notify: no contract found for trade_no={out_trade_no}"
        )
        return "failure"

    # ---- 5. Validate amount before accepting any terminal notification ----
    try:
        expected_amount = f"{float(contract.rentValue):.2f}"
    except (ValueError, TypeError):
        logger.error(
            f"Alipay notify: invalid contract rentValue for trade_no={out_trade_no}"
        )
        return "failure"

    try:
        received_amount = Decimal(str(total_amount_str)).quantize(Decimal("0.01"))
        contract_amount = Decimal(str(contract.rentValue)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError):
        return "failure"
    if received_amount != contract_amount:
        logger.warning(
            f"Alipay notify amount mismatch: trade_no={out_trade_no}, "
            f"expected={expected_amount}, got={total_amount_str}"
        )
        return "failure"

    # ---- 6. Idempotency and late-success reconciliation ----
    if contract.payment_status in {"paid", "reconciliation_required", "refunded"}:
        return "success"

    now = utc_now_naive()
    late_or_closed = contract.payment_status in {"expired", "cancelled"} or (
        contract.payment_status == "pending" and pending_contract_is_expired(contract, now)
    )
    if late_or_closed:
        try:
            if contract.payment_status == "pending":
                if contract.expires_at is None:
                    contract.expires_at = pending_deadline(contract) or now
                _release_reservation(db, contract, "expired")
            contract.payment_status = "reconciliation_required"
            contract.payment_notified_at = now
            contract.payment_notify_trade_no = data.get("trade_no")
            contract.payment_notify_amount = received_amount
            contract.reconciliation_reason = "payment_success_after_contract_closed"
            db.commit()
            invalidate_house_caches(contract.houseId)
            logger.warning(
                "Trusted payment success requires reconciliation: contract_id=%s",
                contract.id,
            )
            return "success"
        except Exception:
            db.rollback()
            logger.exception("Failed to persist payment reconciliation state")
            return "failure"
    if contract.payment_status != "pending":
        logger.warning("Alipay notify received for an unsupported contract state")
        return "failure"

    # ---- 7. Update contract payment status ----
    try:
        contract.payment_notified_at = now
        contract.payment_notify_trade_no = data.get("trade_no")
        contract.payment_notify_amount = received_amount
        contract.reconciliation_reason = None
        _confirm_paid(db, contract)
        db.commit()
        logger.info(
            f"Alipay payment confirmed: trade_no={out_trade_no}, "
            f"contract_id={contract.id}, amount={expected_amount}"
        )
    except Exception:
        db.rollback()
        logger.exception(
            f"Alipay notify: failed to update contract for trade_no={out_trade_no}"
        )
        return "failure"

    return "success"


@router.get("/payments/reconciliation", response_model=APIResponse[list])
def list_payment_reconciliations(
    db: Session = Depends(get_db),
    _admin: UserModel = Depends(get_current_admin),
):
    """List unresolved trusted late-payment notifications for administrators."""

    contracts = (
        db.query(Contract)
        .filter(Contract.payment_status == "reconciliation_required")
        .order_by(Contract.payment_notified_at.asc(), Contract.id.asc())
        .limit(100)
        .all()
    )
    return APIResponse(data=[contract.to_dict() for contract in contracts], message="查询成功")


@router.post("/payments/{contract_id}/reconcile", response_model=APIResponse[dict])
def resolve_payment_reconciliation(
    contract_id: int,
    body: ReconciliationRequest,
    db: Session = Depends(get_db),
    admin: UserModel = Depends(get_current_admin),
):
    """Resolve a trusted late payment without bypassing current occupancy."""

    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id)
        .with_for_update()
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.payment_status != "reconciliation_required":
        raise HTTPException(status_code=409, detail="合同当前不需要支付对账")

    now = utc_now_naive()
    if body.action == "accept_payment":
        if contract.houseId is None or contract.endDate is None or contract.endDate < now:
            raise HTTPException(status_code=409, detail="合同已失效，不能接受该笔支付，请完成退款")
        house = (
            db.query(HouseInfo)
            .filter(HouseInfo.id == contract.houseId)
            .with_for_update()
            .first()
        )
        if house is None:
            raise HTTPException(status_code=409, detail="合同关联房源不存在，请完成退款")
        if (
            house.ownership_status != "verified"
            or house.landlord_id is None
            or house.landlord_id != contract.landlordId
        ):
            raise HTTPException(status_code=409, detail="房源归属与合同不一致，请完成退款")
        if house.available != 1 or house_has_active_occupancy(
            db, house.id, now, exclude_contract_id=contract.id
        ):
            raise HTTPException(status_code=409, detail="房源已被占用或下架，不能接受支付，请完成退款")
        _ensure_rental(db, contract)
        contract.payment_status = "paid"
        contract.paid_at = now
        resolution = "accepted"
    else:
        # This records that an administrator has completed the refund through
        # the provider; it intentionally does not call a mock or real refund API.
        contract.payment_status = "refunded"
        resolution = "refunded"

    contract.reconciled_at = now
    contract.reconciled_by = admin.id
    contract.reconciliation_resolution = resolution
    contract.reconciliation_note = body.note.strip()
    try:
        db.commit()
        db.refresh(contract)
        invalidate_house_caches(contract.houseId)
    except Exception:
        db.rollback()
        logger.exception("Failed to resolve payment reconciliation for contract_id=%s", contract_id)
        raise HTTPException(status_code=500, detail="保存对账结果失败，请稍后重试")
    return APIResponse(data=contract.to_dict(), message="支付对账已处理")


@router.post("/payments/{contract_id}/cancel", response_model=APIResponse)
def cancel_payment(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Cancel an unpaid contract and make the house available again."""
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id)
        .with_for_update()
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.tenantId != current_user.id:
        raise HTTPException(status_code=403, detail="无权取消该合同")
    if contract.payment_status != "pending":
        raise HTTPException(status_code=409, detail="只有待支付合同可以取消")
    try:
        _release_reservation(db, contract, "cancelled")
        db.commit()
        invalidate_house_caches(contract.houseId)
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel contract_id=%s", contract_id)
        raise HTTPException(status_code=500, detail="取消合同失败，请稍后重试")
    return APIResponse(data=contract.to_dict(), message="合同已取消")


@router.post("/payments/{contract_id}/expire", response_model=APIResponse)
def expire_payment(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Release an overdue pending contract on demand.

    This endpoint makes expiry independently verifiable without relying on a
    later payment or lease request to trigger opportunistic cleanup.
    """
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id)
        .with_for_update()
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.tenantId != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作该合同")
    if contract.payment_status != "pending":
        raise HTTPException(status_code=409, detail="合同当前不能过期释放")
    now = utc_now_naive()
    if not pending_contract_is_expired(contract, now):
        raise HTTPException(status_code=409, detail="合同尚未过期")
    try:
        if contract.expires_at is None:
            contract.expires_at = pending_deadline(contract) or now
        _release_reservation(db, contract, "expired")
        db.commit()
        invalidate_house_caches(contract.houseId)
    except Exception:
        db.rollback()
        logger.exception("Failed to expire contract_id=%s", contract_id)
        raise HTTPException(status_code=500, detail="过期释放失败，请稍后重试")
    return APIResponse(data=contract.to_dict(), message="合同已过期，房源已释放")


@router.post("/payments/{contract_id}/mock-confirm", response_model=APIResponse)
def mock_confirm_payment(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Local-only payment confirmation; never weakens the public callback."""
    if not settings.DEBUG or not settings.PAYMENT_MOCK_ENABLED:
        raise HTTPException(status_code=404, detail="接口不存在")
    _expire_pending(db)
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id)
        .with_for_update()
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    if contract.tenantId != current_user.id:
        raise HTTPException(status_code=403, detail="无权确认该合同")
    try:
        _confirm_paid(db, contract)
        db.commit()
    except ValueError:
        db.rollback()
        raise HTTPException(status_code=409, detail="合同已取消或过期")
    return APIResponse(data=contract.to_dict(), message="本地模拟支付成功")
