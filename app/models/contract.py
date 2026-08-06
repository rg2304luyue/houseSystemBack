"""ContractModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Contract(Base):
    __tablename__ = "contract"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rentValue: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(String(255))
    startDate: Mapped[datetime] = mapped_column(DateTime)
    endDate: Mapped[datetime] = mapped_column(DateTime)
    landlordName: Mapped[str] = mapped_column(String(255))
    landlordId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    landlordPhone: Mapped[str] = mapped_column(String(255))
    tenantName: Mapped[str] = mapped_column(String(255))
    tenantId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tenantPhone: Mapped[str] = mapped_column(String(255))
    formattedRent: Mapped[str] = mapped_column(String(255))
    currentDate: Mapped[datetime] = mapped_column(DateTime)
    houseId: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    # Payment tracking (added for P1 payment fix)
    payment_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="pending",
                                                           server_default="pending")
    payment_trade_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "rentValue": self.rentValue,
            "purpose": self.purpose,
            "startDate": self.startDate.strftime("%Y-%m-%d") if self.startDate else None,
            "endDate": self.endDate.strftime("%Y-%m-%d") if self.endDate else None,
            "landlordName": self.landlordName,
            "landlordId": self.landlordId,
            "landlordPhone": self.landlordPhone,
            "tenantName": self.tenantName,
            "tenantId": self.tenantId,
            "tenantPhone": self.tenantPhone,
            "formattedRent": self.formattedRent,
            "currentDate": self.currentDate.strftime("%Y-%m-%d") if self.currentDate else None,
            "houseId": self.houseId,
            "payment_status": self.payment_status,
            "payment_trade_no": self.payment_trade_no,
            "paid_at": self.paid_at.strftime("%Y-%m-%d %H:%M:%S") if self.paid_at else None,
            "expires_at": self.expires_at.strftime("%Y-%m-%d %H:%M:%S") if self.expires_at else None,
        }
