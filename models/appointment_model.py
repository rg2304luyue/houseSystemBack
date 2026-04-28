from typing import Optional
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from exts.db import db
from datetime import datetime

class AppointmentModel(db.Model):
    __tablename__ = 'appointment'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    property: Mapped[Optional[str]] = mapped_column(String(255))
    time: Mapped[datetime] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "property": self.property,
            "time": self.time.strftime("%Y-%m-%d %H:%M:%S") if self.time else None
        }