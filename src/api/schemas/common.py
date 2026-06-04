"""Common API response schemas."""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional details")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[T]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int):
        total_pages = (total + page_size - 1) // page_size
        return cls(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime
    updated_at: datetime