from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from exts import db

class Contract(db.Model):
    __tablename__ = 'contract'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rentValue: Mapped[str] = mapped_column(String(255))
    purpose: Mapped[str] = mapped_column(String(255))
    startDate: Mapped[str] = mapped_column(DateTime)
    endDate: Mapped[str] = mapped_column(DateTime)
    landlordName: Mapped[str] = mapped_column(String(255))
    landlordId: Mapped[str] = mapped_column(String(255))
    landlordPhone: Mapped[str] = mapped_column(String(255))
    tenantName: Mapped[str] = mapped_column(String(255))
    tenantId: Mapped[str] = mapped_column(String(255))
    tenantPhone: Mapped[str] = mapped_column(String(255))
    formattedRent: Mapped[str] = mapped_column(String(255))
    currentDate: Mapped[str] = mapped_column(DateTime)
    houseId: Mapped[int] = mapped_column(Integer, nullable=True, index=True)

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
            "currentDate": self.currentDate.strftime("%Y-%m-%d") if self.currentDate else None
            ,"houseId": self.houseId
        }
