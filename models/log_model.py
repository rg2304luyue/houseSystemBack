from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from exts.db import db

class LogEntry(db.Model):
    __tablename__ = 'log_entries'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    level: Mapped[str] = mapped_column(String(50), index=True)
    module: Mapped[str] = mapped_column(String(100))
    func_name: Mapped[str] = mapped_column(String(100))
    line_no: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)
    traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f'<LogEntry {self.timestamp} [{self.level}] {self.message[:50]}>'
