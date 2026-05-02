from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from exts import db

class News(db.Model):
    __tablename__ = 'news'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    publish_time: Mapped[datetime] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
        }
