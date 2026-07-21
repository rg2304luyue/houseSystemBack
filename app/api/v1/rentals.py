"""Rental routes: list current tenant's rental records.

GET /api/v1/leases/mine
    Returns all rental records belonging to the authenticated user,
    enriched with contract details and house information.

Security:
    - Tenant identity is derived from the JWT token only (never from URL params)
    - Only the authenticated user's own rental records are returned
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.contract import Contract
from app.models.house import HouseInfo
from app.models.rental import Rental
from app.models.user import UserModel
from app.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rentals"])


# ---------------------------------------------------------------------------
# GET /leases/mine
# ---------------------------------------------------------------------------


@router.get("/leases/mine", response_model=APIResponse[list])
def get_my_rentals(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Return the authenticated user's rental records.

    Each record is enriched with:
    - contract: full Contract.to_dict() for the matching house
    - house:   full HouseInfo.to_dict() for the matching house

    Tenant identity comes exclusively from the JWT token.
    """
    # Stable identity comes from the authenticated user's immutable database ID.
    rental_records = (
        db.query(Rental)
        .filter(Rental.tenant_id == current_user.id)
        .all()
    )

    if not rental_records:
        return APIResponse(data=[], message="暂无租赁记录")

    result = []
    for rental in rental_records:
        # Enrich with contract
        contract = db.get(Contract, rental.contract_id) if rental.contract_id else None

        # Enrich with house
        house = db.get(HouseInfo, rental.house_id)

        entry = rental.to_dict()
        entry["contract"] = contract.to_dict() if contract else None
        entry["house"] = house.to_dict() if house else None
        result.append(entry)

    return APIResponse(data=result, message="查询成功")
