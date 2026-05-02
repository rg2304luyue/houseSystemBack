from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from exts import db

class Message(db.Model):
    __tablename__ = 'message'

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(String(500), comment='消息内容')
    sender_username: Mapped[str] = mapped_column(String(50), comment='发送者用户名')
    receiver_username: Mapped[str] = mapped_column(String(50), comment='接收者用户名')
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment='消息时间戳')
    channel_id: Mapped[int] = mapped_column(Integer)

    def to_dict(self):
        return {
            "message_id": self.message_id,
            "content": self.content,
            "sender_username": self.sender_username,
            "receiver_username": self.receiver_username,
            "timestamp": self.timestamp.isoformat() + "Z",
            "channel_id": self.channel_id
        }
