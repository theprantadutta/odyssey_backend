# Odyssey Backend API

Portfolio-grade travel journal backend with FastAPI and PostgreSQL.

## Features

- 🔐 JWT Authentication
- 🗺️ Trip management with photo locations
- 📝 Drag-and-drop itinerary planning
- 📸 Cloudinary image uploads
- 🐳 Docker Compose setup
- 📊 PostgreSQL database with Alembic migrations

## Tech Stack

- **Framework:** FastAPI 0.115.5
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose)
- **Image Storage:** Cloudinary
- **Server:** Uvicorn

## Project Structure

```
odyssey_backend/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── core/             # Security & dependencies
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── config.py         # Settings
│   ├── database.py       # Database setup
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── docker-compose.yml    # Docker setup
├── Dockerfile
└── requirements.txt
```

## Quick Start

### 1. Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database credentials
- JWT secret key (32+ characters)
- Cloudinary credentials (sign up at https://cloudinary.com)

### 2. Run with Docker Compose (Recommended)

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database on port 5432
- Backend API on port 8000

### 3. Run Locally (Without Docker)

**Prerequisites:**
- Python 3.11+
- PostgreSQL running locally

**Install dependencies:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Run migrations:**

```bash
alembic upgrade head
```

**Start server:**

```bash
python run.py
```

## API Documentation

Once running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback migration:

```bash
alembic downgrade -1
```

## API Endpoints

### Authentication ✅
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - Logout

### Trips ✅
- `GET /api/v1/trips` - List all trips (paginated)
- `POST /api/v1/trips` - Create trip
- `GET /api/v1/trips/{id}` - Get trip details
- `PATCH /api/v1/trips/{id}` - Update trip
- `DELETE /api/v1/trips/{id}` - Delete trip

### Activities ✅
- `GET /api/v1/activities` - List activities for a trip
- `POST /api/v1/activities` - Create activity
- `PUT /api/v1/activities/reorder` - Bulk reorder (drag-and-drop)
- `PATCH /api/v1/activities/{id}` - Update activity
- `DELETE /api/v1/activities/{id}` - Delete activity

### Memories ✅
- `GET /api/v1/memories` - List memories for a trip
- `POST /api/v1/memories` - Upload photo with GPS location
- `DELETE /api/v1/memories/{id}` - Delete memory

### Seed Data ✅
- `POST /api/v1/seed/demo-data` - Generate demo data (5 trips, activities, memories)

**📚 Full API Documentation:** See [API_ENDPOINTS.md](API_ENDPOINTS.md) for detailed examples and request/response formats

## Development

**Running tests:**

```bash
pytest
```

**Code formatting:**

```bash
black app/
```

**Linting:**

```bash
flake8 app/
```

## License

MIT License - Built as a portfolio project

## Author

Portfolio project demonstrating FastAPI, Clean Architecture, and production-grade backend development.
