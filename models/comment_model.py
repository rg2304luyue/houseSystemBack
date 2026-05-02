from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, DateTime
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import Mapped, mapped_column
from exts import db

class Comment(db.Model):
    __tablename__ = 'comment'

    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    house_id: Mapped[int] = mapped_column(Integer, comment='房屋的id')
    username: Mapped[str] = mapped_column(VARCHAR(255), comment='留言人名字')
    type: Mapped[int] = mapped_column(Integer, comment='留言人类型,1:租客，2:房东')
    desc: Mapped[str] = mapped_column(VARCHAR(255), comment='留言内容')
    time: Mapped[datetime] = mapped_column(DateTime, comment='留言时间')
    at: Mapped[Optional[int]] = mapped_column(Integer, comment='@哪条留言，前端显示为@谁，选填')
