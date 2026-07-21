"""Shared response schemas — maintains Flask contract {code, data, message, success}."""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    code: int = 200
    data: Optional[T] = None
    message: str = "success"
    success: bool = True


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
