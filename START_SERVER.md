# How to Start Odyssey Backend

## Quick Start

```bash
# Navigate to backend directory
cd G:\MyProjects\odyssey_backend

# Activate virtual environment
.\venv\Scripts\activate

# Start the server
python run.py
```

The server will start on http://localhost:8000

## Test the API

### Health Check
```bash
curl http://localhost:8000/health
```

### API Documentation
Open in browser: http://localhost:8000/docs

### Test User Created
- Email: test@odyssey.com
- Password: test123456

### Test Auth Flow

**Register:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","password":"password123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@odyssey.com","password":"test123456"}'
```

**Get Current User (requires token):**
```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Database

- **Host:** pranta.vps.webdock.cloud
- **Port:** 5432
- **Database Name:** odyssey
- **Shared with:** pinpoint_backend

## Important Notes

- Backend runs on port **8000**
- Uses the same PostgreSQL instance as pinpoint_backend
- Database is on the cloud (not local Docker)
- Migrations are already applied
- Virtual environment is already set up

## Stop the Server

Press `CTRL+C` in the terminal where the server is running

## Re-run Migrations (if needed)

```bash
cd G:\MyProjects\odyssey_backend
.\venv\Scripts\activate
alembic upgrade head
```
