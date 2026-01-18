"""Review API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app import crud
from app.database import db
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter(prefix="/groomers", tags=["reviews"])


@router.post("/{groomer_id}/reviews", response_model=ReviewRead, status_code=201)
def create_review(
    groomer_id: UUID,
    review: ReviewCreate,
) -> ReviewRead:
    """
    Submit a review for a groomer.

    Args:
        groomer_id: Groomer UUID
        review: Review creation data

    Returns:
        Created review

    Raises:
        HTTPException: 404 if groomer not found
    """
    with db.session_scope() as session:
        created_review = crud.create_review(session, groomer_id, review)
        if not created_review:
            raise HTTPException(status_code=404, detail="Groomer not found")
        session.expunge(created_review)
    return created_review


@router.get("/{groomer_id}/reviews", response_model=list[ReviewRead])
def get_groomer_reviews(
    groomer_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
) -> list[ReviewRead]:
    """
    Get all reviews for a groomer.

    Args:
        groomer_id: Groomer UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of reviews
    """
    with db.session_scope() as session:
        reviews = crud.get_groomer_reviews(session, groomer_id, skip=skip, limit=limit)
        for review in reviews:
            session.expunge(review)
    return reviews
