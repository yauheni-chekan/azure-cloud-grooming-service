"""Pytest fixtures for testing."""

import os
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import DatabaseManager
from app.models.base import Base

# Set testing environment variable before importing app
os.environ["TESTING"] = "1"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine for unit tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Session:
    """Create a test database session for unit tests."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """Create a test client with mocked database for API tests."""
    from fastapi.testclient import TestClient

    from app.main import app

    # Create tables
    Base.metadata.create_all(bind=db_engine)

    # Create a test database manager
    test_db_manager = DatabaseManager(db_engine)

    # Patch the global db object
    with (
        patch("app.api.v1.groomers.db", test_db_manager),
        patch("app.api.v1.reviews.db", test_db_manager),
        TestClient(app) as test_client,
    ):
        yield test_client

    Base.metadata.drop_all(bind=db_engine)
