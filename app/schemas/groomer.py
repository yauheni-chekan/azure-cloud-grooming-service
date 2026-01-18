"""Groomer Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GroomerBase(BaseModel):
    """Base groomer schema with common fields."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=255)
    specialization: str | None = Field(None, max_length=255)


class GroomerCreate(GroomerBase):
    """Schema for creating a new groomer."""

    pass


class GroomerUpdate(BaseModel):
    """Schema for updating a groomer (all fields optional)."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    location: str | None = Field(None, min_length=1, max_length=255)
    specialization: str | None = Field(None, max_length=255)


class GroomerRead(GroomerBase):
    """Schema for reading groomer data."""

    groomer_id: UUID
    status: str
    rating: float
    review_count: int
    complaint_count: int
    total_bookings_count: int

    model_config = ConfigDict(from_attributes=True)
