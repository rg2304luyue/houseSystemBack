"""Shared database predicates for contract occupancy and legacy expiry."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.house import HouseInfo
from app.models.rental import Rental


PENDING_RESERVATION_TTL = timedelta(minutes=30)


def active_contract_condition(now: datetime):
    """Return the SQL condition for a reservation or paid active contract.

    Contracts created before ``expires_at`` existed use ``currentDate + 30m``
    as their deterministic reservation deadline. A row with neither timestamp
    is not allowed to reserve a house forever.
    """

    legacy_cutoff = now - PENDING_RESERVATION_TTL
    pending_active = and_(
        Contract.payment_status == "pending",
        or_(
            Contract.expires_at > now,
            and_(
                Contract.expires_at.is_(None),
                Contract.currentDate.is_not(None),
                Contract.currentDate > legacy_cutoff,
            ),
        ),
    )
    paid_active = and_(
        Contract.payment_status == "paid",
        or_(Contract.endDate.is_(None), Contract.endDate >= now.replace(hour=0, minute=0, second=0, microsecond=0)),
    )
    return or_(pending_active, paid_active)


def expired_pending_condition(now: datetime):
    """Return pending rows whose explicit or legacy deadline has elapsed."""

    legacy_cutoff = now - PENDING_RESERVATION_TTL
    return and_(
        Contract.payment_status == "pending",
        or_(
            Contract.expires_at <= now,
            and_(
                Contract.expires_at.is_(None),
                or_(
                    Contract.currentDate.is_(None),
                    Contract.currentDate <= legacy_cutoff,
                ),
            ),
        ),
    )


def pending_deadline(contract: Contract) -> datetime | None:
    """Resolve the explicit or legacy reservation deadline for one row."""

    if contract.expires_at is not None:
        return contract.expires_at
    if contract.currentDate is not None:
        return contract.currentDate + PENDING_RESERVATION_TTL
    return None


def pending_contract_is_expired(contract: Contract, now: datetime) -> bool:
    """Treat an unbounded pending row as expired instead of reserving forever."""

    deadline = pending_deadline(contract)
    return deadline is None or deadline <= now


def active_rental_condition(now: datetime):
    """Return the conservative active condition used for legacy rentals."""

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return or_(
        Rental.contract_id.is_(None),
        Contract.endDate.is_(None),
        Contract.endDate >= day_start,
    )


def market_available_house_condition(now: datetime):
    """Exclude rows that the write-side occupancy guard considers occupied."""

    active_contract = exists(
        select(Contract.id).where(
            Contract.houseId == HouseInfo.id,
            active_contract_condition(now),
        )
    )
    active_rental = exists(
        select(Rental.id)
        .select_from(Rental)
        .outerjoin(Contract, Rental.contract_id == Contract.id)
        .where(
            Rental.house_id == HouseInfo.id,
            active_rental_condition(now),
        )
    )
    return and_(HouseInfo.available == 1, ~active_contract, ~active_rental)


def house_has_active_occupancy(
    db: Session,
    house_id: int,
    now: datetime | None = None,
    *,
    exclude_contract_id: int | None = None,
) -> bool:
    """Check command-side occupancy after the caller has locked the house row."""

    checked_at = now or datetime.now()
    contract_query = db.query(Contract.id).filter(
        Contract.houseId == house_id,
        active_contract_condition(checked_at),
    )
    if exclude_contract_id is not None:
        contract_query = contract_query.filter(Contract.id != exclude_contract_id)
    if contract_query.first() is not None:
        return True

    rental_query = (
        db.query(Rental.id)
        .outerjoin(Contract, Rental.contract_id == Contract.id)
        .filter(Rental.house_id == house_id, active_rental_condition(checked_at))
    )
    if exclude_contract_id is not None:
        rental_query = rental_query.filter(
            or_(Rental.contract_id.is_(None), Rental.contract_id != exclude_contract_id)
        )
    return rental_query.first() is not None
