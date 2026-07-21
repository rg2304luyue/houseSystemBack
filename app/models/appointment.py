"""AppointmentModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AppointmentModel(Base):
    __tablename__ = "appointment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    property: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    time: Mapped[datetime] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "property": self.property,
            "time": self.time.strftime("%Y-%m-%d %H:%M:%S") if self.time else None,
        }
