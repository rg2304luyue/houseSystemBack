"""ContractModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime, Numeric
from sqlalchemy.dialects.mysql import INTEGER as MYSQL_INTEGER
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
    landlordId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user_info.id", ondelete="SET NULL"), nullable=True, index=True)
    landlordPhone: Mapped[str] = mapped_column(String(255))
    tenantName: Mapped[str] = mapped_column(String(255))
    tenantId: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("user_info.id", ondelete="SET NULL"), nullable=True, index=True)
    tenantPhone: Mapped[str] = mapped_column(String(255))
    formattedRent: Mapped[str] = mapped_column(String(255))
    currentDate: Mapped[datetime] = mapped_column(DateTime)
    houseId: Mapped[Optional[int]] = mapped_column(MYSQL_INTEGER(unsigned=True), ForeignKey("house_info.id", ondelete="RESTRICT"), nullable=True, index=True)
    # Payment tracking (added for P1 payment fix)
    payment_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="pending",
                                                           server_default="pending")
    payment_trade_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    payment_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payment_notify_trade_no: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payment_notify_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    reconciliation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reconciled_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("user_info.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reconciliation_resolution: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    reconciliation_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

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
            "payment_notified_at": self.payment_notified_at.strftime("%Y-%m-%d %H:%M:%S") if self.payment_notified_at else None,
            "payment_notify_trade_no": self.payment_notify_trade_no,
            "payment_notify_amount": str(self.payment_notify_amount) if self.payment_notify_amount is not None else None,
            "reconciliation_reason": self.reconciliation_reason,
            "reconciled_at": self.reconciled_at.strftime("%Y-%m-%d %H:%M:%S") if self.reconciled_at else None,
            "reconciled_by": self.reconciled_by,
            "reconciliation_resolution": self.reconciliation_resolution,
            "reconciliation_note": self.reconciliation_note,
        }
