"""CRUD operations for Groomer and Review models."""

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.groomer import Groomer, GroomerStatus
from app.models.review import Review
from app.schemas.groomer import GroomerCreate, GroomerUpdate
from app.schemas.review import ReviewCreate


def create_groomer(db: Session, groomer_in: GroomerCreate) -> Groomer:
    """
    Create a new groomer.

    Args:
        db: Database session
        groomer_in: Groomer creation data

    Returns:
        Created groomer instance
    """
    groomer = Groomer(**groomer_in.model_dump())
    db.add(groomer)
    db.commit()
    db.refresh(groomer)
    return groomer


def get_groomer(db: Session, groomer_id: UUID) -> Groomer | None:
    """
    Get a groomer by ID (excludes deleted groomers).

    Args:
        db: Database session
        groomer_id: Groomer UUID

    Returns:
        Groomer instance or None if not found
    """
    return (
        db.query(Groomer)
        .filter(Groomer.groomer_id == groomer_id, Groomer.status != GroomerStatus.deleted)
        .first()
    )


def get_all_groomers(db: Session, skip: int = 0, limit: int = 100) -> list[Groomer]:
    """
    Get all active groomers.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of groomer instances
    """
    return (
        db.query(Groomer)
        .filter(Groomer.status == GroomerStatus.active)
        .order_by(Groomer.groomer_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_groomer(db: Session, groomer_id: UUID, groomer_update: GroomerUpdate) -> Groomer | None:
    """
    Update a groomer's information.

    Args:
        db: Database session
        groomer_id: Groomer UUID
        groomer_update: Updated groomer data

    Returns:
        Updated groomer instance or None if not found
    """
    groomer = get_groomer(db, groomer_id)
    if not groomer:
        return None

    update_data = groomer_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(groomer, field, value)

    db.commit()
    db.refresh(groomer)
    return groomer


def soft_delete_groomer(db: Session, groomer_id: UUID) -> Groomer | None:
    """
    Soft delete a groomer by setting status to deleted.

    Args:
        db: Database session
        groomer_id: Groomer UUID

    Returns:
        Deleted groomer instance or None if not found
    """
    groomer = db.query(Groomer).filter(Groomer.groomer_id == groomer_id).first()
    if not groomer:
        return None

    groomer.status = GroomerStatus.deleted
    db.commit()
    db.refresh(groomer)
    return groomer


def search_groomers(
    db: Session,
    location: str | None = None,
    specialization: str | None = None,
    min_rating: float | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Groomer]:
    """
    Search groomers with optional filters.

    Args:
        db: Database session
        location: Filter by location (case-insensitive partial match)
        specialization: Filter by specialization (case-insensitive partial match)
        min_rating: Filter by minimum rating
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of matching groomer instances
    """
    query = db.query(Groomer).filter(Groomer.status == GroomerStatus.active)

    if location:
        query = query.filter(Groomer.location.ilike(f"%{location}%"))

    if specialization:
        query = query.filter(Groomer.specialization.ilike(f"%{specialization}%"))

    if min_rating is not None:
        query = query.filter(Groomer.rating >= min_rating)

    return query.order_by(Groomer.rating.desc(), Groomer.groomer_id).offset(skip).limit(limit).all()


def create_review(db: Session, groomer_id: UUID, review_in: ReviewCreate) -> Review | None:
    """
    Create a review for a groomer and recalculate the groomer's rating.

    Args:
        db: Database session
        groomer_id: Groomer UUID
        review_in: Review creation data

    Returns:
        Created review instance or None if groomer not found
    """
    groomer = get_groomer(db, groomer_id)
    if not groomer:
        return None

    # Create the review
    review = Review(groomer_id=groomer_id, **review_in.model_dump())
    db.add(review)
    db.flush()  # Flush to make the review visible in the same transaction

    # Recalculate groomer rating (including the new review)
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.groomer_id == groomer_id).scalar()

    groomer.rating = float(avg_rating) if avg_rating else 0.0
    groomer.review_count = (
        db.query(func.count(Review.review_id)).filter(Review.groomer_id == groomer_id).scalar()
    )

    db.commit()
    db.refresh(review)
    db.refresh(groomer)

    return review


def get_groomer_reviews(
    db: Session, groomer_id: UUID, skip: int = 0, limit: int = 100
) -> list[Review]:
    """
    Get all reviews for a groomer.

    Args:
        db: Database session
        groomer_id: Groomer UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of review instances
    """
    return (
        db.query(Review)
        .filter(Review.groomer_id == groomer_id)
        .order_by(Review.created_at.desc(), Review.review_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
