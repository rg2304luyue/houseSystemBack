"""Shared input normalization and validation helpers."""

import re
from datetime import date, datetime, time

from fastapi import HTTPException


def normalize_email(email: str) -> str:
    """Return a normalized email address or raise a client-facing 400."""
    normalized = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise HTTPException(status_code=400, detail="Invalid email address")
    return normalized


def parse_iso_date_midnight(value: str) -> datetime:
    """Parse an ISO calendar date and return a naive midnight datetime."""
    try:
        return datetime.combine(date.fromisoformat(value), time.min)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
