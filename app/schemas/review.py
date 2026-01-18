"""Review Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    """Base review schema with common fields."""

    booking_id: UUID
    user_id: UUID
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: str | None = Field(None, max_length=500)


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""

    pass


class ReviewRead(ReviewBase):
    """Schema for reading review data."""

    review_id: UUID
    groomer_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
