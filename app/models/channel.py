"""ChannelModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ChannelModel(Base):
    __tablename__ = "channel"

    channel_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_username: Mapped[str] = mapped_column(String(50), comment="租客用户名")
    landlord_username: Mapped[str] = mapped_column(String(50), comment="房东用户名")
    tenant_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    landlord_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "channel_id": self.channel_id,
            "tenant_username": self.tenant_username,
            "landlord_username": self.landlord_username,
            "tenant_id": self.tenant_id,
            "landlord_id": self.landlord_id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
