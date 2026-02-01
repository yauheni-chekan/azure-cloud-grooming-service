"""Tests for review operations and API endpoints."""

from uuid import uuid4

from sqlalchemy.orm import Session

from app import crud
from app.schemas.groomer import GroomerCreate
from app.schemas.review import ReviewCreate


def test_create_review(db_session: Session):
    """Test creating a review for a groomer."""
    groomer_data = GroomerCreate(
        first_name="Review", last_name="Test", location="Test City", specialization="Dogs"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    review_data = ReviewCreate(
        booking_id=uuid4(), user_id=uuid4(), rating=5, comment="Excellent service!"
    )
    review = crud.create_review(db_session, groomer.groomer_id, review_data)

    assert review is not None
    assert review.rating == 5
    assert review.comment == "Excellent service!"
    assert review.groomer_id == groomer.groomer_id


def test_create_review_updates_groomer_rating(db_session: Session):
    """Test that creating a review updates the groomer's rating."""
    groomer_data = GroomerCreate(
        first_name="Rating", last_name="Update", location="Test City", specialization="Cats"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    # Add first review
    review1 = ReviewCreate(booking_id=uuid4(), user_id=uuid4(), rating=5, comment="Great!")
    crud.create_review(db_session, groomer.groomer_id, review1)

    # Check groomer rating
    updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
    assert updated_groomer.rating == 5.0
    assert updated_groomer.review_count == 1


def test_rating_calculation_multiple_reviews(db_session: Session):
    """Test rating calculation with multiple reviews."""
    groomer_data = GroomerCreate(
        first_name="Multi", last_name="Review", location="Test City", specialization="Birds"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    # Add multiple reviews
    ratings = [5, 4, 3, 5, 4]
    for rating in ratings:
        review = ReviewCreate(
            booking_id=uuid4(), user_id=uuid4(), rating=rating, comment=f"Rating {rating}"
        )
        crud.create_review(db_session, groomer.groomer_id, review)

    # Check groomer rating (average)
    updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
    expected_avg = sum(ratings) / len(ratings)
    assert abs(updated_groomer.rating - expected_avg) < 0.01
    assert updated_groomer.review_count == len(ratings)


def test_review_count_increment(db_session: Session):
    """Test that review count increments correctly."""
    groomer_data = GroomerCreate(
        first_name="Count", last_name="Test", location="Test City", specialization="Dogs"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    assert groomer.review_count == 0

    # Add reviews one by one
    for i in range(3):
        review = ReviewCreate(
            booking_id=uuid4(), user_id=uuid4(), rating=4, comment=f"Review {i + 1}"
        )
        crud.create_review(db_session, groomer.groomer_id, review)

        updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
        assert updated_groomer.review_count == i + 1


def test_get_groomer_reviews(db_session: Session):
    """Test getting all reviews for a groomer."""
    groomer_data = GroomerCreate(
        first_name="Get", last_name="Reviews", location="Test City", specialization="Cats"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    # Add multiple reviews
    for i in range(3):
        review = ReviewCreate(
            booking_id=uuid4(), user_id=uuid4(), rating=i + 3, comment=f"Comment {i + 1}"
        )
        crud.create_review(db_session, groomer.groomer_id, review)

    # Get all reviews
    reviews = crud.get_groomer_reviews(db_session, groomer.groomer_id)

    assert len(reviews) == 3
    assert all(r.groomer_id == groomer.groomer_id for r in reviews)


def test_create_review_for_nonexistent_groomer(db_session: Session):
    """Test creating a review for a non-existent groomer."""
    non_existent_id = uuid4()
    review_data = ReviewCreate(booking_id=uuid4(), user_id=uuid4(), rating=4, comment="Test")

    review = crud.create_review(db_session, non_existent_id, review_data)

    assert review is None


def test_review_rating_validation(client):
    """Test review rating validation (must be 1-5)."""
    # Create a groomer via API
    create_response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "Validation",
            "last_name": "Test",
            "location": "Test City",
            "specialization": "Dogs",
        },
    )
    groomer_id = create_response.json()["groomer_id"]

    # Test invalid rating (too low)
    response = client.post(
        f"/api/v1/groomers/{groomer_id}/reviews",
        json={
            "booking_id": str(uuid4()),
            "user_id": str(uuid4()),
            "rating": 0,
            "comment": "Invalid",
        },
    )
    assert response.status_code == 422

    # Test invalid rating (too high)
    response = client.post(
        f"/api/v1/groomers/{groomer_id}/reviews",
        json={
            "booking_id": str(uuid4()),
            "user_id": str(uuid4()),
            "rating": 6,
            "comment": "Invalid",
        },
    )
    assert response.status_code == 422

    # Test valid rating
    response = client.post(
        f"/api/v1/groomers/{groomer_id}/reviews",
        json={"booking_id": str(uuid4()), "user_id": str(uuid4()), "rating": 5, "comment": "Valid"},
    )
    assert response.status_code == 201


def test_review_api_create(client):
    """Test creating a review via API."""
    # Create a groomer via API
    create_response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "API",
            "last_name": "Review",
            "location": "Test City",
            "specialization": "Birds",
        },
    )
    groomer_id = create_response.json()["groomer_id"]

    # Create a review
    response = client.post(
        f"/api/v1/groomers/{groomer_id}/reviews",
        json={
            "booking_id": str(uuid4()),
            "user_id": str(uuid4()),
            "rating": 4,
            "comment": "Good service",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["rating"] == 4
    assert data["comment"] == "Good service"
    assert "review_id" in data


def test_review_api_create_for_nonexistent_groomer(client):
    """Test creating a review for non-existent groomer via API."""
    non_existent_id = uuid4()

    response = client.post(
        f"/api/v1/groomers/{non_existent_id}/reviews",
        json={"booking_id": str(uuid4()), "user_id": str(uuid4()), "rating": 4, "comment": "Test"},
    )

    assert response.status_code == 404


def test_review_api_get_reviews(client):
    """Test getting reviews for a groomer via API."""
    # Create a groomer via API
    create_response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "API",
            "last_name": "Get",
            "location": "Test City",
            "specialization": "Dogs",
        },
    )
    groomer_id = create_response.json()["groomer_id"]

    # Add reviews via API
    for i in range(3):
        client.post(
            f"/api/v1/groomers/{groomer_id}/reviews",
            json={
                "booking_id": str(uuid4()),
                "user_id": str(uuid4()),
                "rating": 5,
                "comment": f"Review {i + 1}",
            },
        )

    # Get all reviews
    response = client.get(f"/api/v1/groomers/{groomer_id}/reviews")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all(r["groomer_id"] == groomer_id for r in data)


def test_rating_with_single_review(db_session: Session):
    """Test rating calculation with a single review."""
    groomer_data = GroomerCreate(
        first_name="Single", last_name="Review", location="Test City", specialization="Cats"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    review = ReviewCreate(booking_id=uuid4(), user_id=uuid4(), rating=3, comment="Average")
    crud.create_review(db_session, groomer.groomer_id, review)

    updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
    assert updated_groomer.rating == 3.0
    assert updated_groomer.review_count == 1


def test_rating_with_no_reviews(db_session: Session):
    """Test that groomer has 0 rating with no reviews."""
    groomer_data = GroomerCreate(
        first_name="No", last_name="Reviews", location="Test City", specialization="Birds"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    assert groomer.rating == 0.0
    assert groomer.review_count == 0


def test_recalculate_groomer_rating(db_session: Session):
    """Test manually recalculating a groomer's rating."""
    groomer_data = GroomerCreate(
        first_name="Recalc", last_name="Test", location="Test City", specialization="Dogs"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    # Add multiple reviews
    ratings = [5, 4, 3, 5, 4]
    for rating in ratings:
        review = ReviewCreate(
            booking_id=uuid4(), user_id=uuid4(), rating=rating, comment=f"Rating {rating}"
        )
        crud.create_review(db_session, groomer.groomer_id, review)

    # Manually recalculate rating
    updated_groomer = crud.recalculate_groomer_rating(db_session, groomer.groomer_id)

    expected_avg = sum(ratings) / len(ratings)
    assert updated_groomer is not None
    assert abs(updated_groomer.rating - expected_avg) < 0.01
    assert updated_groomer.review_count == len(ratings)


def test_delete_review_updates_rating(db_session: Session):
    """Test that deleting a review updates the groomer's rating."""
    groomer_data = GroomerCreate(
        first_name="Delete", last_name="Review", location="Test City", specialization="Cats"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    # Add multiple reviews
    review1 = ReviewCreate(booking_id=uuid4(), user_id=uuid4(), rating=5, comment="Excellent!")
    review2 = ReviewCreate(booking_id=uuid4(), user_id=uuid4(), rating=3, comment="Average")
    review3 = ReviewCreate(booking_id=uuid4(), user_id=uuid4(), rating=4, comment="Good")

    crud.create_review(db_session, groomer.groomer_id, review1)
    created_review2 = crud.create_review(db_session, groomer.groomer_id, review2)
    crud.create_review(db_session, groomer.groomer_id, review3)

    # Check initial rating (5+3+4)/3 = 4.0
    updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
    assert abs(updated_groomer.rating - 4.0) < 0.01
    assert updated_groomer.review_count == 3

    # Delete the review with rating 3
    deleted_review = crud.delete_review(db_session, created_review2.review_id)
    assert deleted_review is not None

    # Check updated rating (5+4)/2 = 4.5
    updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
    assert abs(updated_groomer.rating - 4.5) < 0.01
    assert updated_groomer.review_count == 2


def test_delete_all_reviews_resets_rating(db_session: Session):
    """Test that deleting all reviews resets the groomer's rating to 0."""
    groomer_data = GroomerCreate(
        first_name="Reset", last_name="Rating", location="Test City", specialization="Birds"
    )
    groomer = crud.create_groomer(db_session, groomer_data)

    # Add a review
    review = ReviewCreate(booking_id=uuid4(), user_id=uuid4(), rating=5, comment="Great!")
    created_review = crud.create_review(db_session, groomer.groomer_id, review)

    # Verify rating is set
    updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
    assert updated_groomer.rating == 5.0
    assert updated_groomer.review_count == 1

    # Delete the review
    crud.delete_review(db_session, created_review.review_id)

    # Verify rating is reset to 0
    updated_groomer = crud.get_groomer(db_session, groomer.groomer_id)
    assert updated_groomer.rating == 0.0
    assert updated_groomer.review_count == 0


def test_delete_nonexistent_review(db_session: Session):
    """Test deleting a non-existent review."""
    non_existent_id = uuid4()
    deleted_review = crud.delete_review(db_session, non_existent_id)
    assert deleted_review is None


def test_review_api_delete(client):
    """Test deleting a review via API."""
    # Create a groomer via API
    create_response = client.post(
        "/api/v1/groomers",
        json={
            "first_name": "API",
            "last_name": "Delete",
            "location": "Test City",
            "specialization": "Dogs",
        },
    )
    groomer_id = create_response.json()["groomer_id"]

    # Create reviews
    client.post(
        f"/api/v1/groomers/{groomer_id}/reviews",
        json={
            "booking_id": str(uuid4()),
            "user_id": str(uuid4()),
            "rating": 5,
            "comment": "Excellent!",
        },
    )

    review2_response = client.post(
        f"/api/v1/groomers/{groomer_id}/reviews",
        json={
            "booking_id": str(uuid4()),
            "user_id": str(uuid4()),
            "rating": 3,
            "comment": "Average",
        },
    )
    review2_id = review2_response.json()["review_id"]

    # Check groomer rating (5+3)/2 = 4.0
    groomer_response = client.get(f"/api/v1/groomers/{groomer_id}")
    assert abs(groomer_response.json()["rating"] - 4.0) < 0.01
    assert groomer_response.json()["review_count"] == 2

    # Delete one review
    delete_response = client.delete(f"/api/v1/groomers/reviews/{review2_id}")
    assert delete_response.status_code == 200

    # Check updated groomer rating (only 5 remains)
    groomer_response = client.get(f"/api/v1/groomers/{groomer_id}")
    assert groomer_response.json()["rating"] == 5.0
    assert groomer_response.json()["review_count"] == 1


def test_review_api_delete_nonexistent(client):
    """Test deleting a non-existent review via API."""
    non_existent_id = uuid4()
    response = client.delete(f"/api/v1/groomers/reviews/{non_existent_id}")
    assert response.status_code == 404
