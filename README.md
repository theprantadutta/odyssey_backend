# Odyssey Backend API

A production-grade travel journal REST API built with FastAPI and PostgreSQL. Powers the Odyssey mobile app with secure authentication, trip management, and photo memories with GPS locations.

![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Authentication** - JWT-based auth with secure password hashing (bcrypt)
- **Trip Management** - Full CRUD with pagination and status tracking
- **Activities** - Itinerary planning with drag-and-drop reordering
- **Memories** - Photo uploads with GPS coordinates via Cloudinary
- **Onboarding** - Optional demo trips for new users
- **Auto Documentation** - Swagger UI and ReDoc included

## Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | FastAPI 0.115.5 |
| **Database** | PostgreSQL 15 |
| **ORM** | SQLAlchemy 2.0.36 |
| **Migrations** | Alembic 1.14 |
| **Auth** | JWT (python-jose) + bcrypt |
| **Validation** | Pydantic 2.10 |
| **Image Storage** | Cloudinary |
| **Server** | Uvicorn |
| **Containerization** | Docker + Docker Compose |

## Project Structure

```
odyssey_backend/
├── app/
│   ├── api/v1/              # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── trips.py         # Trip CRUD + default trips
│   │   ├── activities.py    # Activity CRUD + reordering
│   │   ├── memories.py      # Photo upload endpoints
│   │   └── seed.py          # Demo data generation
│   ├── core/                # Core utilities
│   │   ├── security.py      # JWT & password hashing
│   │   ├── dependencies.py  # FastAPI dependencies
│   │   └── cloudinary.py    # Image upload service
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── trip.py
│   │   ├── activity.py
│   │   └── memory.py
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic layer
│   ├── config.py            # Environment settings
│   ├── database.py          # Database connection
│   └── main.py              # FastAPI app initialization
├── alembic/                 # Database migrations
├── Dockerfile
├── compose.yml
├── requirements.txt
└── .env.example
```

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone and configure**
   ```bash
   git clone https://github.com/yourusername/odyssey_backend.git
   cd odyssey_backend
   cp .env.example .env
   ```

2. **Edit `.env`** with your settings:
   ```env
   DATABASE_PASSWORD=your-secure-password
   JWT_SECRET_KEY=your-secret-key-min-32-characters
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-api-key
   CLOUDINARY_API_SECRET=your-api-secret
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

   This starts:
   - PostgreSQL on port `5432`
   - Backend API on port `8546`

4. **Access the API**
   - Swagger UI: http://localhost:8546/docs
   - ReDoc: http://localhost:8546/redoc
   - Health Check: http://localhost:8546/health

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- PostgreSQL 15+

1. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Cloudinary credentials
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start server**
   ```bash
   python run.py
   ```

   Or with auto-reload:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8546 --reload
   ```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/login` | Login and get JWT token |
| `GET` | `/api/v1/auth/me` | Get current user info |
| `POST` | `/api/v1/auth/logout` | Logout (client-side) |

**Register/Login Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Trips

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/trips` | List trips (paginated) |
| `POST` | `/api/v1/trips` | Create new trip |
| `GET` | `/api/v1/trips/{id}` | Get trip by ID |
| `PATCH` | `/api/v1/trips/{id}` | Update trip |
| `DELETE` | `/api/v1/trips/{id}` | Delete trip |
| `POST` | `/api/v1/trips/default-trips` | Create demo trips for onboarding |

**Create Trip Request:**
```json
{
  "title": "Weekend in Paris",
  "description": "A romantic getaway...",
  "cover_image_url": "https://...",
  "start_date": "2024-03-15",
  "end_date": "2024-03-18",
  "status": "planned",
  "tags": ["europe", "romantic", "city"]
}
```

**Trip Status Values:** `planned`, `ongoing`, `completed`

### Activities

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/activities?trip_id={id}` | List activities for trip |
| `POST` | `/api/v1/activities` | Create activity |
| `PATCH` | `/api/v1/activities/{id}` | Update activity |
| `DELETE` | `/api/v1/activities/{id}` | Delete activity |
| `PUT` | `/api/v1/activities/reorder?trip_id={id}` | Bulk reorder |

**Activity Categories:** `food`, `travel`, `stay`, `explore`

**Reorder Request:**
```json
{
  "activity_orders": [
    {"id": "uuid-1", "sort_order": 0},
    {"id": "uuid-2", "sort_order": 1},
    {"id": "uuid-3", "sort_order": 2}
  ]
}
```

### Memories (Photo Locations)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/memories?trip_id={id}` | List memories for trip |
| `POST` | `/api/v1/memories` | Upload photo with location |
| `DELETE` | `/api/v1/memories/{id}` | Delete memory |

**Upload Memory (multipart/form-data):**
- `trip_id`: UUID
- `photo`: File
- `latitude`: Decimal
- `longitude`: Decimal
- `caption`: String (optional)
- `taken_at`: DateTime (optional)

### Seed Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/seed/demo-data` | Generate 5 demo trips with activities and memories |

## Database Schema

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   users     │     │   trips     │     │ activities  │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ id (PK)     │────<│ user_id(FK) │     │ trip_id(FK) │>────┐
│ email       │     │ id (PK)     │────<│ id (PK)     │     │
│ password    │     │ title       │     │ title       │     │
│ is_active   │     │ description │     │ category    │     │
│ created_at  │     │ status      │     │ sort_order  │     │
└─────────────┘     │ tags[]      │     │ latitude    │     │
                    │ start_date  │     │ longitude   │     │
                    │ end_date    │     └─────────────┘     │
                    └─────────────┘                         │
                          │                                 │
                          │         ┌─────────────┐         │
                          └────────>│  memories   │<────────┘
                                    ├─────────────┤
                                    │ trip_id(FK) │
                                    │ id (PK)     │
                                    │ photo_url   │
                                    │ latitude    │
                                    │ longitude   │
                                    │ caption     │
                                    └─────────────┘
```

**Relationships:**
- User → Trips (1:N, cascade delete)
- Trip → Activities (1:N, cascade delete)
- Trip → Memories (1:N, cascade delete)

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `odyssey` |
| `DATABASE_USERNAME` | Database user | `postgres` |
| `DATABASE_PASSWORD` | Database password | - |
| `JWT_SECRET_KEY` | JWT signing key (32+ chars) | - |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `10080` (7 days) |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name | - |
| `CLOUDINARY_API_KEY` | Cloudinary API key | - |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret | - |
| `ALLOWED_ORIGINS` | CORS origins | `*` |
| `DEBUG` | Enable debug mode | `True` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8546` |

## Development

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=app
```

### Code Formatting

```bash
# Format code
black app/

# Sort imports
isort app/
```

### Linting

```bash
flake8 app/
```

## Deployment

### Docker Production Build

```bash
docker build -t odyssey-backend:latest .
docker run -p 8546:8546 --env-file .env odyssey-backend:latest
```

### With Traefik (HTTPS)

The `compose.yml` includes Traefik labels for automatic HTTPS:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.odyssey.rule=Host(`odyssey.yourdomain.com`)"
  - "traefik.http.routers.odyssey.tls.certresolver=letsencrypt"
```

## Security Features

- **Password Hashing**: bcrypt with automatic salting
- **JWT Tokens**: HS256 algorithm, configurable expiry
- **CORS**: Configurable allowed origins
- **SQL Injection**: Protected via SQLAlchemy ORM
- **Input Validation**: Pydantic schema validation
- **Cascade Delete**: Prevents orphaned records

## Error Responses

```json
{
  "detail": "Error message here"
}
```

| Status | Description |
|--------|-------------|
| `400` | Bad request / validation error |
| `401` | Invalid or missing token |
| `403` | Account disabled |
| `404` | Resource not found |
| `409` | Conflict (e.g., duplicate email) |
| `422` | Validation error |
| `500` | Server error |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [Odyssey Mobile App](../odyssey) - Flutter frontend for this API

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [Pydantic](https://pydantic.dev/) - Data validation
- [Cloudinary](https://cloudinary.com/) - Image management
