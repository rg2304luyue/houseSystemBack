"""AppointmentModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from typing import Optional
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.mysql import INTEGER as MYSQL_INTEGER
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.time import utc_now_naive


class AppointmentModel(Base):
    __tablename__ = "appointment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    property: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time: Mapped[datetime] = mapped_column(DateTime)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user_info.id", ondelete="SET NULL"), nullable=True, index=True
    )
    house_id: Mapped[Optional[int]] = mapped_column(
        MYSQL_INTEGER(unsigned=True), ForeignKey("house_info.id", ondelete="SET NULL"), nullable=True, index=True
    )
    landlord_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user_info.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "property": self.property,
            "time": self.time.strftime("%Y-%m-%d %H:%M:%S") if self.time else None,
            "user_id": self.user_id,
            "house_id": self.house_id,
            "landlord_id": self.landlord_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
