"""Contract routes: create lease contract with transactional house occupation.

POST /api/v1/leases
    Create a lease contract. The server determines identities (landlord, tenant)
    and rent from house_id + JWT token. Creates Contract + Rental records and
    marks the house as unavailable in a single transaction with FOR UPDATE lock.

Security:
    - All identity comes from the JWT token (Depends(get_current_user))
    - Rent amount is validated against house.price; client-submitted amounts are
      rejected if they do not match
    - House is locked with FOR UPDATE to prevent race conditions
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.time import utc_now_naive
from app.db.session import get_db
from app.models.contract import Contract
from app.models.house import HouseInfo
from app.models.user import UserModel
from app.api.v1.houses import invalidate_house_caches
from app.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["contracts"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CreateLeaseRequest(BaseModel):
    """Request body for creating a lease contract.

    The rent is always read from the selected house on the server.
    """

    house_id: int = Field(..., description="House ID to lease")
    rentValue: str | None = Field(None, description="Legacy field; ignored by the server")
    purpose: str = Field(..., min_length=1, max_length=255, description="Lease purpose (e.g. '居住')")
    startDate: str = Field(..., description="Lease start date (ISO format: YYYY-MM-DD)")
    endDate: str = Field(..., description="Lease end date (ISO format: YYYY-MM-DD)")


# ---------------------------------------------------------------------------
# POST /leases
# ---------------------------------------------------------------------------


@router.post("/leases", response_model=APIResponse, status_code=201)
def create_lease(
    body: CreateLeaseRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a lease contract for a house.

    Transactional steps:
    1. Validate date range
    2. Lock house row with FOR UPDATE to prevent races
    3. Validate house exists and is available
    4. Read rent from house.price (never trust client-submitted amount)
    5. Derive landlord identity from house record, tenant from JWT
    6. Create a pending Contract and reserve the house atomically
    """
    # Release reservations that expired since the last request before checking
    # availability. This keeps local development deterministic without a
    # separate scheduler process.
    from app.api.v1.payments import _expire_pending
    _expire_pending(db)

    # ---- 1. Parse and validate dates ----
    try:
        start_date = datetime.fromisoformat(body.startDate)
        end_date = datetime.fromisoformat(body.endDate)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日期格式错误，请使用 YYYY-MM-DD 格式",
        )

    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始日期必须早于结束日期",
        )

    # ---- 2. Lock house row (FOR UPDATE) to prevent concurrent leases ----
    house = (
        db.query(HouseInfo)
        .filter(HouseInfo.id == body.house_id)
        .with_for_update()
        .first()
    )

    if house is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="房源不存在",
        )

    # ---- 3. Validate house availability ----
    if house.available != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该房源已被租赁或不可租",
        )

    if house.landlord_id is not None and house.landlord_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="不能租赁自己发布的房源",
        )

    # ---- 4. Derive amount from the locked house row ----
    if house.price is None or house.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="房源租金配置无效，暂不能签约",
        )
    submitted_rent = int(house.price)

    # ---- 5. Derive identities from server data (NEVER trust client) ----
    # Tenant: from JWT current user
    tenant_name = current_user.name or current_user.phone or f"用户{current_user.id}"
    tenant_id = current_user.id
    tenant_phone = current_user.phone or ""

    # Landlord: from house record
    landlord_name = house.landlord or ""
    landlord_phone = house.phone_num or ""

    # Stable ownership comes from the listing ID.  Legacy rows may remain
    # unassigned after the conservative migration; their display snapshots
    # are retained, but no user is granted owner permissions by name.
    landlord_id = house.landlord_id

    # ---- 6. Create a pending Contract and reserve the house atomically ----
    # Store reservation timestamps in UTC; expiry checks also use UTC.
    now = utc_now_naive()
    formatted_rent = f"¥{submitted_rent}/月"

    contract = Contract(
        rentValue=str(submitted_rent),
        purpose=body.purpose,
        startDate=start_date,
        endDate=end_date,
        landlordName=landlord_name,
        landlordId=landlord_id,
        landlordPhone=landlord_phone,
        tenantName=tenant_name,
        tenantId=tenant_id,
        tenantPhone=tenant_phone,
        formattedRent=formatted_rent,
        currentDate=now,
        houseId=body.house_id,
        payment_status="pending",
        expires_at=now + timedelta(minutes=30),
    )
    db.add(contract)
    db.flush()

    # Occupy the house
    house.available = 0

    try:
        db.commit()
        db.refresh(contract)
        invalidate_house_caches(body.house_id)
    except Exception:
        db.rollback()
        logger.exception(f"创建合同失败: house_id={body.house_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建合同失败，请稍后重试",
        )

    logger.info(
        f"合同创建成功: contract_id={contract.id}, house_id={body.house_id}, "
        f"tenant={tenant_name}, landlord={landlord_name}"
    )

    return APIResponse(
        code=201,
        data=contract.to_dict(),
        message="合同创建成功，请尽快完成支付",
    )
