"""MessageModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class MessageModel(Base):
    __tablename__ = "message"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String(500), comment="消息内容")
    sender_username: Mapped[str] = mapped_column(String(50), comment="发送者用户名")
    receiver_username: Mapped[str] = mapped_column(String(50), comment="接收者用户名")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="消息时间戳")
    sender_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    receiver_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    channel_id: Mapped[int] = mapped_column(Integer)

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "content": self.content,
            "sender_username": self.sender_username,
            "receiver_username": self.receiver_username,
            "timestamp": self.timestamp.isoformat() + "Z",
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "channel_id": self.channel_id,
        }
