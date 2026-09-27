"""Appointment routes — ported from Flask blueprint appointment.py."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.appointment import AppointmentModel
from app.models.user import UserModel
from app.models.house import HouseInfo
from app.core.time import utc_now_naive
from app.api.deps import get_current_user
from app.schemas.common import APIResponse
from app.services.occupancy import market_available_house_condition

router = APIRouter()


class CreateAppointmentRequest(BaseModel):
    house_id: int = Field(..., gt=0, description="房源ID")
    time: str = Field(..., description="预约时间，ISO8601格式")


class AppointmentResponse(BaseModel):
    id: int
    username: str | None = None
    property: str | None = None
    time: str | None = None
    user_id: int | None = None
    house_id: int | None = None
    landlord_id: int | None = None
    status: str = "pending"
    created_at: str | None = None
    updated_at: str | None = None


@router.post("/appointments", response_model=APIResponse[AppointmentResponse])
def create_appointment(
    body: CreateAppointmentRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a viewing appointment.

    The authenticated user's identity is used as the username;
    the client cannot override it.
    """
    try:
        appointment_time = datetime.fromisoformat(body.time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误"
        )

    if appointment_time.tzinfo is not None:
        appointment_time = appointment_time.astimezone(timezone.utc).replace(tzinfo=None)
    if appointment_time <= utc_now_naive():
        raise HTTPException(status_code=400, detail="预约时间必须晚于当前时间")

    house = db.query(HouseInfo).filter(HouseInfo.id == body.house_id).with_for_update().first()
    if house is None:
        raise HTTPException(status_code=404, detail="房源不存在")
    if (house.ownership_status or "pending") == "rejected":
        raise HTTPException(status_code=409, detail="该房源归属核验未通过，暂不可预约")
    if not house.available:
        raise HTTPException(status_code=409, detail="该房源当前不可预约")
    if db.query(HouseInfo.id).filter(
        HouseInfo.id == house.id,
        market_available_house_condition(utc_now_naive()),
    ).first() is None:
        raise HTTPException(status_code=409, detail="该房源已被预订或出租，暂不可预约")
    if house.landlord_id == current_user.id:
        raise HTTPException(status_code=409, detail="不能预约自己发布的房源")
    # Lock both participants in stable ID order. Together with the house lock,
    # this serializes same-user and same-landlord bookings across houses.
    participant_ids = {current_user.id}
    if house.landlord_id is not None:
        participant_ids.add(house.landlord_id)
    db.query(UserModel.id).filter(
        UserModel.id.in_(sorted(participant_ids))
    ).order_by(UserModel.id).with_for_update().all()
    conflict_conditions = [
        AppointmentModel.house_id == body.house_id,
        AppointmentModel.user_id == current_user.id,
    ]
    # A legacy imported listing may only have a contact snapshot, not a linked
    # platform landlord. Do not compare NULL landlord IDs: that would make an
    # appointment for one legacy listing conflict with every other such listing.
    if house.landlord_id is not None:
        conflict_conditions.append(AppointmentModel.landlord_id == house.landlord_id)
    conflict = db.query(AppointmentModel.id).filter(
        AppointmentModel.time == appointment_time,
        AppointmentModel.status.in_(("pending", "confirmed")),
        or_(*conflict_conditions),
    ).first()
    if conflict:
        raise HTTPException(status_code=409, detail="该房源或您在此时间已有预约")

    appointment = AppointmentModel(
        username=current_user.name or current_user.phone,
        property=house.title or house.community or f"房源{house.id}",
        time=appointment_time,
        user_id=current_user.id,
        house_id=house.id,
        landlord_id=house.landlord_id,
        status="pending",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return APIResponse(
        code=201,
        data=AppointmentResponse(**appointment.to_dict()),
        message=(
            "预约提交成功，平台将协助联系房源发布方"
            if house.landlord_id is None
            else "预约提交成功"
        ),
    )
