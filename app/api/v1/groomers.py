"""Groomer API endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app import crud
from app.database import db
from app.schemas.groomer import GroomerCreate, GroomerRead, GroomerUpdate
from app.unified_log_queue import log_sender

router = APIRouter(prefix="/groomers", tags=["groomers"])


@router.post("", response_model=GroomerRead, status_code=201)
async def create_groomer(
    groomer: GroomerCreate,
) -> GroomerRead:
    """
    Create a new groomer.

    Args:
        groomer: Groomer creation data

    Returns:
        Created groomer
    """
    with db.session_scope() as session:
        result = crud.create_groomer(session, groomer)
        session.refresh(result)
        session.expunge(result)
        if log_sender:
            await log_sender.send(
                level="info",
                event="grooming-service.groomer.created",
                message="Groomer created",
                context={
                    "groomer_id": result.groomer_id,
                    "groomer_name": f"{result.first_name} {result.last_name}",
                },
            )
        return result


@router.get("/{groomer_id}", response_model=GroomerRead)
async def get_groomer(
    groomer_id: UUID,
) -> GroomerRead:
    """
    Get a groomer by ID.

    Args:
        groomer_id: Groomer UUID

    Returns:
        Groomer data

    Raises:
        HTTPException: 404 if groomer not found
    """
    with db.session_scope() as session:
        groomer = crud.get_groomer(session, groomer_id)
        if not groomer:
            raise HTTPException(status_code=404, detail="Groomer not found")
        session.expunge(groomer)
    return groomer


@router.put("/{groomer_id}", response_model=GroomerRead)
async def update_groomer(
    groomer_id: UUID,
    groomer_update: GroomerUpdate,
) -> GroomerRead:
    """
    Update a groomer's information.

    Args:
        groomer_id: Groomer UUID
        groomer_update: Updated groomer data

    Returns:
        Updated groomer

    Raises:
        HTTPException: 404 if groomer not found
    """
    with db.session_scope() as session:
        groomer = crud.update_groomer(session, groomer_id, groomer_update)
        if not groomer:
            raise HTTPException(status_code=404, detail="Groomer not found")
        session.expunge(groomer)
    if log_sender:
        await log_sender.send(
            level="info",
            event="grooming-service.groomer.updated",
            message="Groomer updated",
            context={
                "groomer_id": groomer_id,
            },
        )
    return groomer


@router.delete("/{groomer_id}", response_model=GroomerRead)
async def delete_groomer(
    groomer_id: UUID,
) -> GroomerRead:
    """
    Soft delete a groomer.

    Args:
        groomer_id: Groomer UUID

    Returns:
        Deleted groomer

    Raises:
        HTTPException: 404 if groomer not found
    """
    with db.session_scope() as session:
        groomer = crud.soft_delete_groomer(session, groomer_id)
        if not groomer:
            raise HTTPException(status_code=404, detail="Groomer not found")
        session.expunge(groomer)
    if log_sender:
        await log_sender.send(
            level="info",
            event="grooming-service.groomer.deleted",
            message="Groomer deleted",
            context={
                "groomer_id": groomer_id,
            },
        )
    return groomer


@router.get("", response_model=list[GroomerRead])
async def search_groomers(
    location: str | None = Query(None, description="Filter by location"),
    specialization: str | None = Query(None, description="Filter by specialization"),
    min_rating: float | None = Query(None, ge=0.0, le=5.0, description="Minimum rating filter"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
) -> list[GroomerRead]:
    """
    Search and filter groomers.

    Args:
        location: Optional location filter (partial match)
        specialization: Optional specialization filter (partial match)
        min_rating: Optional minimum rating filter
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of matching groomers
    """
    with db.session_scope() as session:
        groomers = crud.search_groomers(
            session,
            location=location,
            specialization=specialization,
            min_rating=min_rating,
            skip=skip,
            limit=limit,
        )
        for groomer in groomers:
            session.expunge(groomer)
    return groomers


@router.post("/{groomer_id}/increment-booking-count")
async def increment_booking_count_endpoint(
    groomer_id: UUID,
) -> GroomerRead:
    """Increment the booking count for a groomer.

    This endpoint is called by the booking service when a new booking is created.

    :param groomer_id: Groomer UUID
    :return: Updated groomer with incremented booking count
    """
    with db.session_scope() as session:
        groomer = crud.increment_booking_count(session, groomer_id)
        if not groomer:
            raise HTTPException(status_code=404, detail="Groomer not found")
        session.expunge(groomer)
    if log_sender:
        await log_sender.send(
            level="info",
            event="grooming-service.groomer.booking_count_incremented",
            message="Groomer booking count incremented",
            context={
                "groomer_id": str(groomer_id),
                "total_bookings_count": groomer.total_bookings_count,
            },
        )
    return GroomerRead.model_validate(groomer, from_attributes=True)
