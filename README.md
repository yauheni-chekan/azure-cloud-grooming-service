# Azure Cloud Grooming Service

A microservice for managing groomer profiles, reviews, and ratings as part of the Azure Cloud Pet Grooming Booking System.

## Overview

The Grooming Service is responsible for:
- Managing groomer profiles (CRUD operations)
- Handling reviews and ratings
- Computing average ratings based on customer feedback
- Supporting groomer search with filters (location, specialization, minimum rating)
- Soft delete functionality for data retention

## Architecture

This service follows a microservices architecture pattern with:
- **FastAPI** for RESTful API
- **SQLAlchemy** for ORM and database management
- **Pydantic** for data validation
- **UV** for dependency management
- **Pytest** for unit testing

### Database Models

#### Groomer
- `groomer_id` (UUID): Primary key
- `first_name`, `last_name`: Groomer name
- `location`: Groomer location
- `specialization`: Area of expertise (optional)
- `status`: active | inactive | deleted
- `rating`: Average rating (0.0-5.0)
- `review_count`: Total number of reviews
- `complaint_count`: Number of complaints
- `total_bookings_count`: Total bookings completed

#### Review
- `review_id` (UUID): Primary key
- `groomer_id` (UUID): Foreign key to Groomer
- `booking_id` (UUID): Reference to booking
- `user_id` (UUID): Reference to user
- `rating` (1-5): Customer rating
- `comment` (optional): Review text
- `created_at`: Timestamp

## API Endpoints

### Groomers

#### Create Groomer
```
POST /api/v1/groomers
```
**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "location": "New York",
  "specialization": "Dogs"
}
```

#### Get Groomer
```
GET /api/v1/groomers/{groomer_id}
```

#### Update Groomer
```
PUT /api/v1/groomers/{groomer_id}
```
**Request Body:** (all fields optional)
```json
{
  "location": "Los Angeles",
  "specialization": "Cats"
}
```

#### Delete Groomer (Soft Delete)
```
DELETE /api/v1/groomers/{groomer_id}
```

#### Search Groomers
```
GET /api/v1/groomers?location=New+York&specialization=Dogs&min_rating=4.0
```
**Query Parameters:**
- `location` (optional): Filter by location (partial match)
- `specialization` (optional): Filter by specialization (partial match)
- `min_rating` (optional): Minimum rating filter (0.0-5.0)
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Max results (default: 100)

### Reviews

#### Submit Review
```
POST /api/v1/groomers/{groomer_id}/reviews
```
**Request Body:**
```json
{
  "booking_id": "uuid",
  "user_id": "uuid",
  "rating": 5,
  "comment": "Excellent service!"
}
```

#### Get Groomer Reviews
```
GET /api/v1/groomers/{groomer_id}/reviews
```

### Health Check
```
GET /api/v1/health
```

## Installation & Setup

### Prerequisites
- Python 3.13+
- UV package manager

### Install UV
```bash
# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup Development Environment

1. Clone the repository
```bash
git clone <repository-url>
cd azure-cloud-grooming-service
```

2. Create virtual environment and install dependencies
```bash
uv venv
uv pip install -e .
uv pip install -e ".[dev]"
```

3. Create `.env` file
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the service
```bash
uv run uvicorn app.main:app --reload
```

The service will be available at `http://localhost:8000`

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run unit tests:
```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
uv run pytest tests/test_groomers.py
```

## Docker

### Build Docker Image
```bash
docker build -t grooming-service .
```

### Run Container
```bash
docker run -p 8000:8000 -e DATABASE_URL="sqlite:///./grooming.db" grooming-service
```

### Docker Compose (example)
```yaml
version: '3.8'
services:
  grooming-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/grooming
    depends_on:
      - db
  db:
    image: postgres:16
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=grooming
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | "Azure Cloud Grooming Service" |
| `APP_VERSION` | Application version | "0.1.0" |
| `DEBUG` | Debug mode | false |
| `DATABASE_URL` | Database connection string | "sqlite:///./grooming_service.db" |
| `API_V1_PREFIX` | API version prefix | "/api/v1" |

## Database Configuration

### SQLite (Development)
```
DATABASE_URL="sqlite:///./grooming_service.db"
```

### Azure SQL Database
```
DATABASE_URL="mssql+pyodbc://username:password@server.database.windows.net/grooming_db?driver=ODBC+Driver+18+for+SQL+Server"
```

### PostgreSQL
```
DATABASE_URL="postgresql://username:password@localhost:5432/grooming_db"
```

## Project Structure

```
azure-cloud-grooming-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database session management
│   ├── crud.py              # CRUD operations
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── groomer.py
│   │   └── review.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── groomer.py
│   │   └── review.py
│   └── api/
│       └── v1/              # API v1 endpoints
│           ├── __init__.py
│           ├── groomers.py
│           ├── reviews.py
│           └── health.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_groomers.py     # Groomer tests
│   └── test_reviews.py      # Review tests
├── pyproject.toml           # UV dependencies
├── Dockerfile
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## Key Features

### Automatic Rating Calculation
When a review is submitted, the groomer's average rating is automatically recalculated based on all reviews.

### Soft Delete
Deleted groomers are marked with status "deleted" but remain in the database for data retention and compliance.

### Search Filters
Search supports multiple optional filters that can be combined:
- Location (case-insensitive partial match)
- Specialization (case-insensitive partial match)
- Minimum rating

### Data Validation
- Review ratings must be between 1-5
- All required fields are validated using Pydantic
- UUID validation for all IDs

## Development

### Code Style
The project follows Python best practices and PEP 8 guidelines.

### Adding New Features
1. Update models if needed (`app/models/`)
2. Add/update schemas (`app/schemas/`)
3. Implement CRUD operations (`app/crud.py`)
4. Create API endpoints (`app/api/v1/`)
5. Write tests (`tests/`)
6. Update documentation

## License

MIT License - See LICENSE file for details.

## Related Services

This service is part of the Azure Cloud Pet Grooming Booking System:
- **BookingService**: Manages bookings and user accounts
- **GroomerService**: Manages groomers and reviews (this service)
- **ComplaintService**: Handles customer complaints

## References

- [Azure Cloud Practice Documentation](https://github.com/yauheni-chekan/azure-cloud-practice/tree/feature/practice-1)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [UV Documentation](https://github.com/astral-sh/uv)