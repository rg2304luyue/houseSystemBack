"""Reviewed, privacy-filtered failure cases for the RAG evaluation loop."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now_naive
from app.db.base import Base


class RAGFailureCase(Base):
    __tablename__ = "rag_failure_case"
    __table_args__ = (UniqueConstraint("request_id", name="uq_rag_failure_case_request_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_agent_run.request_id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_info.id", ondelete="CASCADE"), nullable=False, index=True
    )
    origin: Mapped[str] = mapped_column(String(20), nullable=False, default="user_feedback")
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    sanitized_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    route: Mapped[str | None] = mapped_column(String(30), nullable=True)
    failure_type: Mapped[str] = mapped_column(String(40), nullable=False)
    index_signature: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retrieval_trace: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    expected_route: Mapped[str | None] = mapped_column(String(30), nullable=True)
    expected_sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
