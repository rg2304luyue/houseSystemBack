from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from exts import db

class Rental(db.Model):
    __tablename__ = 'rental'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_username: Mapped[str] = mapped_column(String(50), nullable=False)
    landlord_username: Mapped[str] = mapped_column(String(50), nullable=False)
    house_id: Mapped[int] = mapped_column(Integer)
    currentDate: Mapped[datetime] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "tenant_username": self.tenant_username,
            "landlord_username": self.landlord_username,
            "house_id": self.house_id,
            "currentDate": self.currentDate.strftime("%Y-%m-%d") if self.currentDate else None,
        }
