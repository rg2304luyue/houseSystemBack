from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from exts import db

class Repair_Complaint(db.Model):
    __tablename__ = 'repair_complaint'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_reason: Mapped[Optional[str]] = mapped_column(String(255))
    house_address: Mapped[Optional[str]] = mapped_column(String(255))
    repair_type: Mapped[Optional[str]] = mapped_column(String(255))
    repair_description: Mapped[Optional[str]] = mapped_column(String(255))
    complaint_content: Mapped[Optional[str]] = mapped_column(String(255))
    complaint_person: Mapped[Optional[str]] = mapped_column(String(255))
    agreed_terms: Mapped[int] = mapped_column(Integer)
    create_at: Mapped[datetime] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "report_reason": self.report_reason,
            "house_address": self.house_address,
            "repair_type": self.repair_type,
            "repair_description": self.repair_description,
            "complaint_content": self.complaint_content,
            "complaint_person": self.complaint_person,
            "agreed_terms": self.agreed_terms,
            "create_at": self.create_at.isoformat() if self.create_at else None
        }
