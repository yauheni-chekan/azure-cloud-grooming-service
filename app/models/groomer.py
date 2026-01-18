"""Groomer database model."""

import enum
import uuid

from sqlalchemy import Column, Enum, Float, Integer, String, Uuid
from sqlalchemy.orm import relationship

from app.models.base import Base


class GroomerStatus(str, enum.Enum):
    """Groomer status enumeration."""

    active = "active"
    inactive = "inactive"
    deleted = "deleted"


class Groomer(Base):
    """Groomer model representing a pet grooming professional."""

    __tablename__ = "groomers"

    groomer_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    specialization = Column(String(255), nullable=True)
    status = Column(Enum(GroomerStatus), default=GroomerStatus.active, nullable=False)
    rating = Column(Float, default=0.0, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    complaint_count = Column(Integer, default=0, nullable=False)
    total_bookings_count = Column(Integer, default=0, nullable=False)

    # Relationships
    reviews = relationship("Review", back_populates="groomer", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Groomer(id={self.groomer_id}, name={self.first_name} {self.last_name}, status={self.status})>"  # noqa: E501
