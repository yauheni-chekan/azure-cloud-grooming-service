"""Review database model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import relationship

from app.models.base import Base


class Review(Base):
    """Review model representing customer feedback for a groomer."""

    __tablename__ = "reviews"

    review_id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    groomer_id = Column(Uuid, ForeignKey("groomers.groomer_id"), nullable=False)
    booking_id = Column(Uuid, nullable=False)
    user_id = Column(Uuid, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # Relationships
    groomer = relationship("Groomer", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review(id={self.review_id}, groomer_id={self.groomer_id}, rating={self.rating})>"
