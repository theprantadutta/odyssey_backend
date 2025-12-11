# Odyssey Backend - Quick Start Guide

This guide will help you get the backend running quickly for development.

## Prerequisites

- Python 3.11+ installed
- Docker and Docker Compose installed (recommended)
- PostgreSQL (if not using Docker)

## Option 1: Run with Docker Compose (Recommended)

### Step 1: Start Services

```bash
cd G:\MyProjects\odyssey_backend
docker-compose up -d
```

This will start:
- PostgreSQL database on `localhost:5432`
- Backend API on `localhost:8546`

### Step 2: Check Logs

```bash
docker-compose logs -f backend
```

### Step 3: Test the API

Open your browser and visit:
- **API Docs:** http://localhost:8546/docs
- **Health Check:** http://localhost:8546/health

### Step 4: Stop Services

```bash
docker-compose down
```

To remove data volumes:

```bash
docker-compose down -v
```

## Option 2: Run Locally (Without Docker)

### Step 1: Install Dependencies

```bash
cd G:\MyProjects\odyssey_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup PostgreSQL

**If you have PostgreSQL installed locally:**

```bash
# Create database
createdb odyssey

# Or using psql:
psql -U postgres
CREATE DATABASE odyssey;
\q
```

**Update `.env` file:**

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=odyssey
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_postgres_password
```

### Step 3: Run Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Step 4: Start the Server

```bash
python run.py
```

The API will be available at http://localhost:8546

## Testing the Auth Flow

### 1. Register a User

```bash
curl -X POST "http://localhost:8546/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. Login

```bash
curl -X POST "http://localhost:8546/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### 3. Get Current User

```bash
# Replace {token} with the access_token from above
curl -X GET "http://localhost:8546/api/v1/auth/me" \
  -H "Authorization: Bearer {token}"
```

## Using Swagger UI (Recommended)

1. Open http://localhost:8546/docs
2. Click "Authorize" button (top right)
3. Enter: `Bearer {your_access_token}`
4. Click "Authorize" and "Close"
5. Now you can test all endpoints with authentication

## Troubleshooting

### Database Connection Error

**Error:** `Could not connect to database`

**Fix:**
- Ensure PostgreSQL is running
- Check `.env` file has correct database credentials
- If using Docker: `docker-compose ps` to check if db container is running

### Migration Error

**Error:** `Target database is not up to date`

**Fix:**
```bash
alembic upgrade head
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Fix:**
- Ensure you're in the `odyssey_backend` directory
- Check that virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

- [ ] Configure Cloudinary credentials in `.env`
- [ ] Implement Trips endpoints (Phase 1)
- [ ] Implement Activities endpoints (Phase 1)
- [ ] Implement Memories endpoints (Phase 1)
- [ ] Create seed data generator (Phase 1)

## Development Tips

### Watch Logs

```bash
# Docker
docker-compose logs -f backend

# Local
# Logs will print to console where you ran python run.py
```

### Rebuild Docker Container

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Reset Database

```bash
# Docker
docker-compose down -v
docker-compose up -d

# Local
dropdb odyssey
createdb odyssey
alembic upgrade head
```

### Generate New Migration

```bash
alembic revision --autogenerate -m "Add new field to Trip model"
alembic upgrade head
```

## API Endpoints

### Authentication (✅ Implemented)
- `POST /api/v1/auth/register` - Register
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get user info
- `POST /api/v1/auth/logout` - Logout

### Trips (🚧 Phase 1)
- Coming soon...

### Activities (🚧 Phase 1)
- Coming soon...

### Memories (🚧 Phase 1)
- Coming soon...

### Seed Data (🚧 Phase 1)
- Coming soon...

---

**Ready for Phase 1?** Once auth is tested, we'll implement the full CRUD endpoints for trips, activities, and memories!
