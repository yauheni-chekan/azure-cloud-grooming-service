"""Tests for groomer CRUD operations and API endpoints."""

from uuid import uuid4

from sqlalchemy.orm import Session

from app import crud
from app.models.groomer import GroomerStatus
from app.schemas.groomer import GroomerCreate, GroomerUpdate


def test_create_groomer(db_session: Session):
    """Test creating a new groomer."""
    groomer_data = GroomerCreate(
        first_name="Alice", last_name="Smith", location="New York", specialization="Dogs"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    assert groomer.first_name == "Alice"
    assert groomer.last_name == "Smith"
    assert groomer.location == "New York"
    assert groomer.specialization == "Dogs"
    assert groomer.status == GroomerStatus.active
    assert groomer.rating == 0.0
    assert groomer.review_count == 0


def test_get_groomer_existing(db_session: Session):
    """Test getting an existing groomer."""
    groomer_data = GroomerCreate(
        first_name="Bob", last_name="Johnson", location="Los Angeles", specialization="Cats"
    )
    created_groomer = crud.create_groomer(db_session, groomer_data)

    fetched_groomer = crud.get_groomer(db_session, created_groomer.groomer_id)

    assert fetched_groomer is not None
    assert fetched_groomer.groomer_id == created_groomer.groomer_id
    assert fetched_groomer.first_name == "Bob"


def test_get_groomer_non_existent(db_session: Session):
    """Test getting a non-existent groomer."""
    non_existent_id = uuid4()
    groomer = crud.get_groomer(db_session, non_existent_id)

    assert groomer is None


def test_update_groomer(db_session: Session):
    """Test updating a groomer's information."""
    groomer_data = GroomerCreate(
        first_name="Charlie", last_name="Brown", location="Chicago", specialization="Birds"
    )
    created_groomer = crud.create_groomer(db_session, groomer_data)

    update_data = GroomerUpdate(location="San Francisco", specialization="All Pets")
    updated_groomer = crud.update_groomer(db_session, created_groomer.groomer_id, update_data)

    assert updated_groomer is not None
    assert updated_groomer.location == "San Francisco"
    assert updated_groomer.specialization == "All Pets"
    assert updated_groomer.first_name == "Charlie"  # Unchanged


def test_soft_delete_groomer(db_session: Session):
    """Test soft deleting a groomer."""
    groomer_data = GroomerCreate(
        first_name="David", last_name="Wilson", location="Boston", specialization="Reptiles"
    )
    created_groomer = crud.create_groomer(db_session, groomer_data)

    deleted_groomer = crud.soft_delete_groomer(db_session, created_groomer.groomer_id)

    assert deleted_groomer is not None
    assert deleted_groomer.status == GroomerStatus.deleted

    # Verify it doesn't appear in normal queries
    fetched_groomer = crud.get_groomer(db_session, created_groomer.groomer_id)
    assert fetched_groomer is None


def test_search_groomers_by_location(db_session: Session):
    """Test searching groomers by location."""
    crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Eva", last_name="Garcia", location="New York", specialization="Dogs"
        ),
    )
    crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Frank", last_name="Miller", location="Los Angeles", specialization="Cats"
        ),
    )
    crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Grace", last_name="Davis", location="New York", specialization="Birds"
        ),
    )

    results = crud.search_groomers(db_session, location="New York")

    assert len(results) == 2
    assert all(g.location == "New York" for g in results)


def test_search_groomers_by_specialization(db_session: Session):
    """Test searching groomers by specialization."""
    crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Henry", last_name="Taylor", location="Seattle", specialization="Dogs"
        ),
    )
    crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Iris", last_name="Anderson", location="Portland", specialization="Cats"
        ),
    )
    crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Jack", last_name="Thomas", location="Denver", specialization="Dogs"
        ),
    )

    results = crud.search_groomers(db_session, specialization="Dogs")

    assert len(results) == 2
    assert all(g.specialization == "Dogs" for g in results)


def test_search_groomers_by_min_rating(db_session: Session):
    """Test searching groomers by minimum rating."""
    groomer1 = crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Kate", last_name="White", location="Miami", specialization="Cats"
        ),
    )
    groomer2 = crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Leo", last_name="Harris", location="Austin", specialization="Dogs"
        ),
    )

    # Manually set ratings for testing
    groomer1.rating = 4.5
    groomer2.rating = 3.0
    db_session.commit()

    results = crud.search_groomers(db_session, min_rating=4.0)

    assert len(results) == 1
    assert results[0].first_name == "Kate"


def test_search_groomers_combined_filters(db_session: Session):
    """Test searching groomers with multiple filters."""
    groomer1 = crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Mike", last_name="Clark", location="New York", specialization="Dogs"
        ),
    )
    groomer2 = crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Nina", last_name="Lewis", location="New York", specialization="Cats"
        ),
    )
    groomer3 = crud.create_groomer(
        db_session,
        GroomerCreate(
            first_name="Oscar", last_name="Walker", location="Chicago", specialization="Dogs"
        ),
    )

    groomer1.rating = 4.5
    groomer2.rating = 4.8
    groomer3.rating = 3.5
    db_session.commit()

    results = crud.search_groomers(db_session, location="New York", min_rating=4.0)

    assert len(results) == 2
    assert all(g.location == "New York" and g.rating >= 4.0 for g in results)


def test_groomer_api_create(client):
    """Test creating a groomer via API."""
    response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "API",
            "last_name": "User",
            "location": "Test City",
            "specialization": "Test Spec",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "API"
    assert data["status"] == "active"
    assert "groomer_id" in data


def test_groomer_api_get(client):
    """Test getting a groomer via API."""
    # First create a groomer via API
    create_response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "Test",
            "last_name": "Groomer",
            "location": "API Town",
            "specialization": "Testing",
        },
    )
    created_groomer = create_response.json()
    groomer_id = created_groomer["groomer_id"]

    # Then get it
    response = client.get(f"/api/v1/groomers/{groomer_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Test"
    assert data["groomer_id"] == groomer_id


def test_groomer_api_get_not_found(client):
    """Test getting a non-existent groomer via API."""
    non_existent_id = uuid4()
    response = client.get(f"/api/v1/groomers/{non_existent_id}")

    assert response.status_code == 404


def test_groomer_api_update(client):
    """Test updating a groomer via API."""
    # First create a groomer via API
    create_response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "Update",
            "last_name": "Test",
            "location": "Before",
            "specialization": "Old",
        },
    )
    groomer_id = create_response.json()["groomer_id"]

    # Then update it
    response = client.put(
        f"/api/v1/groomers/{groomer_id}", json={"location": "After", "specialization": "New"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "After"
    assert data["specialization"] == "New"
    assert data["first_name"] == "Update"  # Unchanged


def test_groomer_api_delete(client):
    """Test deleting a groomer via API."""
    # First create a groomer via API
    create_response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "Delete",
            "last_name": "Me",
            "location": "Temp",
            "specialization": "Temp",
        },
    )
    groomer_id = create_response.json()["groomer_id"]

    # Then delete it
    response = client.delete(f"/api/v1/groomers/{groomer_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"

    # Verify it's not accessible anymore
    get_response = client.get(f"/api/v1/groomers/{groomer_id}")
    assert get_response.status_code == 404


def test_groomer_api_search(client):
    """Test searching groomers via API."""
    # Create groomers via API
    client.post(
        "/api/v1/groomers",
        json={
            "first_name": "Search1",
            "last_name": "Test",
            "location": "SearchCity",
            "specialization": "Dogs",
        },
    )
    client.post(
        "/api/v1/groomers",
        json={
            "first_name": "Search2",
            "last_name": "Test",
            "location": "OtherCity",
            "specialization": "Cats",
        },
    )

    # Search by location
    response = client.get("/api/v1/groomers?location=SearchCity")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["location"] == "SearchCity"
