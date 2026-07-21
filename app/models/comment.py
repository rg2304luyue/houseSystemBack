"""CommentModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CommentModel(Base):
    __tablename__ = "comment"

    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    house_id: Mapped[int] = mapped_column(Integer, comment="房屋的id")
    username: Mapped[str] = mapped_column(String(255), comment="留言人名字")
    type: Mapped[int] = mapped_column(Integer, comment="留言人类型,1:租客,2:房东")
    desc: Mapped[str] = mapped_column(String(255), comment="留言内容")
    time: Mapped[datetime] = mapped_column(DateTime, comment="留言时间")
    at: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="@哪条留言,前端显示为@谁,选填")

    def to_dict(self) -> dict:
        return {
            "comment_id": self.comment_id,
            "house_id": self.house_id,
            "username": self.username,
            "type": self.type,
            "desc": self.desc,
            "time": self.time.isoformat() if self.time else None,
            "at": self.at,
        }
