"""UserModel — ported from Flask-SQLAlchemy to SQLAlchemy 2.x DeclarativeBase."""
from typing import Optional
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.security import hash_password, verify_password


class UserModel(Base):
    __tablename__ = "user_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    addr: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    seen_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    collect_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    identityCard: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    userType: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avatarUrl: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def set_password(self, password_text: str):
        self.password = hash_password(password_text)

    def check_password(self, password_text: str) -> bool:
        return verify_password(password_text, self.password or "")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "addr": self.addr,
            "seen_id": self.seen_id,
            "collect_id": self.collect_id,
            "identityCard": self._masked_identity_card(),
            "userType": self.userType,
            "avatarUrl": self.avatarUrl,
        }

    def _masked_identity_card(self) -> Optional[str]:
        """Mask the ID number (keep first 6 / last 4) before it leaves the API."""
        card = self.identityCard
        if not card or len(card) <= 10:
            return card
        return f"{card[:6]}{'*' * (len(card) - 10)}{card[-4:]}"
