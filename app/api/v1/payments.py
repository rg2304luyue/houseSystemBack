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
from app.core.time import utc_now_naive

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.contract import Contract
from app.models.house import HouseInfo
from app.models.rental import Rental
from app.models.user import UserModel
from app.api.v1.houses import invalidate_house_caches
from app.core.config import settings
from app.schemas.common import APIResponse

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


def _release_reservation(db: Session, contract: Contract, new_status: str) -> None:
    """Release a pending reservation without touching paid rental history."""
    contract.payment_status = new_status
    if contract.houseId is not None:
        house = (
            db.query(HouseInfo)
            .filter(HouseInfo.id == contract.houseId)
            .with_for_update()
            .first()
        )
        if house is not None:
            house.available = 1


def _expire_pending(db: Session, now: datetime | None = None) -> None:
    """Expire overdue reservations opportunistically on payment operations."""
    now = now or utc_now_naive()
    overdue = db.query(Contract).filter(
        Contract.payment_status == "pending",
        Contract.expires_at.is_not(None),
        Contract.expires_at <= now,
    ).with_for_update(skip_locked=True).all()
    for contract in overdue:
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


def _confirm_paid(db: Session, contract: Contract) -> None:
    """Confirm a contract exactly once and create its rental record."""
    if contract.payment_status == "paid":
        return
    if contract.payment_status != "pending":
        raise ValueError("contract is no longer payable")
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
        ))
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
    if contract.payment_status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该合同已完成支付，请勿重复支付",
        )
    if contract.payment_status in ("cancelled", "expired"):
        raise HTTPException(status_code=409, detail="合同已取消或过期，请重新签约")
    if contract.expires_at is not None and contract.expires_at <= utc_now_naive():
        _release_reservation(db, contract, "expired")
        db.commit()
        invalidate_house_caches(contract.houseId)
        raise HTTPException(status_code=409, detail="合同已过期，请重新签约")

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

    # ---- 5. Read amount from contract (NEVER from client) ----
    try:
        total_amount = float(contract.rentValue)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="合同金额格式错误",
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
            detail=f"生成支付链接失败: {e}",
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

    # ---- 1. Verify signature (skip in sandbox/dev) ----
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

    # ---- 5. Idempotent check: already paid ----
    if contract.payment_status == "paid":
        logger.info(
            f"Alipay notify: already paid (idempotent): "
            f"trade_no={out_trade_no}, contract_id={contract.id}"
        )
        return "success"
    if contract.payment_status != "pending":
        logger.warning("Alipay notify received for a non-payable contract")
        return "failure"
    if contract.expires_at is not None and contract.expires_at <= utc_now_naive():
        try:
            _release_reservation(db, contract, "expired")
            db.commit()
            invalidate_house_caches(contract.houseId)
        except Exception:
            db.rollback()
            logger.exception("Alipay notify failed to release expired reservation")
        return "failure"

    # ---- 6. Validate amount (prevent amount tampering) ----
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

    # ---- 7. Update contract payment status ----
    try:
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
    if contract.payment_status == "paid":
        raise HTTPException(status_code=409, detail="已支付合同不能取消")
    if contract.payment_status == "pending":
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
    if contract.expires_at is None or contract.expires_at > utc_now_naive():
        raise HTTPException(status_code=409, detail="合同尚未过期")
    try:
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
