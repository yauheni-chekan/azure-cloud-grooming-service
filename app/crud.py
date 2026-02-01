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


def recalculate_groomer_rating(db: Session, groomer_id: UUID) -> Groomer | None:
    """
    Recalculate a groomer's rating based on all their reviews.

    This function computes the average rating from all reviews and updates
    the groomer's rating and review_count fields.

    Args:
        db: Database session
        groomer_id: Groomer UUID

    Returns:
        Updated groomer instance or None if groomer not found
    """
    groomer = get_groomer(db, groomer_id)
    if not groomer:
        return None

    # Calculate average rating from all reviews
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.groomer_id == groomer_id).scalar()

    # Update groomer rating and review count
    groomer.rating = round(float(avg_rating), 2) if avg_rating else 0.0
    groomer.review_count = (
        db.query(func.count(Review.review_id)).filter(Review.groomer_id == groomer_id).scalar()
    )

    db.commit()
    db.refresh(groomer)
    return groomer


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
    recalculate_groomer_rating(db, groomer_id)

    db.refresh(review)
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


def delete_review(db: Session, review_id: UUID) -> Review | None:
    """
    Delete a review and recalculate the groomer's rating.

    Args:
        db: Database session
        review_id: Review UUID

    Returns:
        Deleted review instance or None if not found
    """
    review = db.query(Review).filter(Review.review_id == review_id).first()
    if not review:
        return None

    groomer_id = review.groomer_id

    # Store review data before deletion
    review_data = {
        "review_id": review.review_id,
        "groomer_id": review.groomer_id,
        "booking_id": review.booking_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at,
    }

    db.delete(review)
    db.flush()

    # Recalculate groomer rating after deletion
    recalculate_groomer_rating(db, groomer_id)

    # Create a detached review object to return
    deleted_review = Review(**review_data)
    return deleted_review


def increment_booking_count(db: Session, groomer_id: UUID) -> Groomer | None:
    """Increment the total_bookings_count for a groomer.

    :param db: Database session
    :param groomer_id: Groomer UUID
    :return: Updated groomer instance or None if not found
    """
    groomer = get_groomer(db, groomer_id)
    if not groomer:
        return None

    groomer.total_bookings_count += 1
    db.commit()
    db.refresh(groomer)
    return groomer
