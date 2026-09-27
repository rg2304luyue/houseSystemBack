"""Derive public appointment/signing capabilities from current database state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.time import utc_now_naive
from app.models.house import HouseInfo
from app.services.occupancy import market_available_house_condition


def market_available_house_ids(db: Session, house_ids: list[int], now: datetime | None = None) -> set[int]:
    """Return market-available IDs in one query to avoid per-card database calls."""

    if not house_ids:
        return set()
    checked_at = now or utc_now_naive()
    rows = db.query(HouseInfo.id).filter(
        HouseInfo.id.in_(house_ids), market_available_house_condition(checked_at)
    ).all()
    return {row[0] for row in rows}


def capability_fields(house: HouseInfo, *, market_available: bool) -> dict[str, object]:
    """Build deterministic public capabilities; clients must not infer them."""

    ownership_status = house.ownership_status or "pending"
    can_appoint = market_available and ownership_status != "rejected"
    can_sign = bool(
        market_available
        and ownership_status == "verified"
        and house.landlord_id is not None
        and (house.price or 0) > 0
    )
    reason: str | None = None
    if not market_available:
        reason = "房源已下架、已预订或已出租"
    elif ownership_status == "rejected":
        reason = "房源归属核验未通过，暂不能在线签约"
    elif ownership_status != "verified" or house.landlord_id is None:
        reason = "房源归属待管理员核验，暂不能在线签约"
    elif (house.price or 0) <= 0:
        reason = "租金信息不完整，暂不能在线签约"
    return {
        "ownership_status": ownership_status,
        "can_appoint": can_appoint,
        "can_sign": can_sign,
        "unavailable_reason": reason,
    }


def public_visible_house_condition():
    """Keep rejected listings out of every public read path."""

    return or_(HouseInfo.ownership_status.is_(None), HouseInfo.ownership_status != "rejected")


def serialize_houses(db: Session, houses: list[HouseInfo], now: datetime | None = None) -> list[dict]:
    """Serialize houses with a database-backed capability snapshot."""

    available_ids = market_available_house_ids(db, [house.id for house in houses], now)
    result = []
    for house in houses:
        item = house.to_dict()
        item.update(capability_fields(house, market_available=house.id in available_ids))
        result.append(item)
    return result
