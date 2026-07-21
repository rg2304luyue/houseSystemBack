"""Appointment routes — ported from Flask blueprint appointment.py."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.models.appointment import AppointmentModel
from app.models.user import UserModel
from app.api.deps import get_current_user
from app.schemas.common import APIResponse

router = APIRouter()


class CreateAppointmentRequest(BaseModel):
    property: str = Field(..., description="房源名称")
    time: str = Field(..., description="预约时间，ISO8601格式")


class AppointmentResponse(BaseModel):
    id: int
    username: str | None = None
    property: str | None = None
    time: str | None = None


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
    # Use the authenticated user's name or phone as the appointment username
    username = current_user.name or current_user.phone

    try:
        appointment_time = datetime.fromisoformat(body.time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误"
        )

    appointment = AppointmentModel(
        username=username,
        property=body.property,
        time=appointment_time,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return APIResponse(
        code=201,
        data=AppointmentResponse(**appointment.to_dict()),
        message="预约提交成功",
    )
