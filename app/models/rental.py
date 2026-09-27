"""RentalModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, String, DateTime, Index
from sqlalchemy.dialects.mysql import INTEGER as MYSQL_INTEGER
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Rental(Base):
    __tablename__ = "rental"
    __table_args__ = (
        Index("uq_rental_contract_id", "contract_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("contract.id", ondelete="RESTRICT"), nullable=True)
    tenant_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user_info.id", ondelete="SET NULL"), nullable=True, index=True)
    landlord_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user_info.id", ondelete="SET NULL"), nullable=True, index=True)
    tenant_username: Mapped[str] = mapped_column(String(50), nullable=False)
    landlord_username: Mapped[str] = mapped_column(String(50), nullable=False)
    house_id: Mapped[int] = mapped_column(MYSQL_INTEGER(unsigned=True), ForeignKey("house_info.id", ondelete="RESTRICT"), index=True)
    currentDate: Mapped[datetime] = mapped_column(DateTime)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="legacy", server_default="legacy")

    def to_dict(self):
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "tenant_id": self.tenant_id,
            "landlord_id": self.landlord_id,
            "tenant_username": self.tenant_username,
            "landlord_username": self.landlord_username,
            "house_id": self.house_id,
            "currentDate": self.currentDate.strftime("%Y-%m-%d") if self.currentDate else None,
            "source": self.source,
            "record_kind": "payment_contract" if self.contract_id is not None else "legacy_history",
        }
