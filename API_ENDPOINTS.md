# Odyssey Backend API Endpoints

## Base URL
```
http://localhost:8546
```

## Authentication

All endpoints except `/health`, `/docs`, and `/auth/*` require JWT authentication.

**Header:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Authentication Endpoints

### Register
```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "uuid-here"
}
```

### Login
```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "uuid-here"
}
```

### Get Current User
```http
GET /api/v1/auth/me
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_active": true
}
```

---

## Trip Endpoints

### List Trips (Paginated)
```http
GET /api/v1/trips/?page=1&page_size=20
```

**Query Parameters:**
- `page` (default: 1) - Page number
- `page_size` (default: 20, max: 100) - Items per page

**Response:**
```json
{
  "trips": [...],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

### Get Trip by ID
```http
GET /api/v1/trips/{trip_id}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Tokyo Adventure",
  "description": "Amazing trip to Tokyo",
  "cover_image_url": "https://...",
  "start_date": "2025-06-01",
  "end_date": "2025-06-10",
  "status": "planned",
  "tags": ["japan", "culture", "food"],
  "created_at": "2025-11-19T...",
  "updated_at": "2025-11-19T..."
}
```

### Create Trip
```http
POST /api/v1/trips/
```

**Request Body:**
```json
{
  "title": "Paris Adventure",
  "description": "Romantic getaway to Paris",
  "cover_image_url": "https://images.unsplash.com/...",
  "start_date": "2025-07-01",
  "end_date": "2025-07-10",
  "status": "planned",
  "tags": ["france", "romance", "culture"]
}
```

### Update Trip
```http
PATCH /api/v1/trips/{trip_id}
```

**Request Body (all fields optional):**
```json
{
  "title": "Updated Title",
  "status": "ongoing"
}
```

### Delete Trip
```http
DELETE /api/v1/trips/{trip_id}
```

**Response:** 204 No Content

---

## Activity Endpoints

### List Activities for Trip
```http
GET /api/v1/activities/?trip_id={trip_id}
```

**Query Parameters:**
- `trip_id` (required) - Trip UUID

**Response:**
```json
{
  "activities": [
    {
      "id": "uuid",
      "trip_id": "uuid",
      "title": "Visit Eiffel Tower",
      "description": "Climb to the top",
      "scheduled_time": "2025-07-02T10:00:00",
      "category": "explore",
      "latitude": "48.8584",
      "longitude": "2.2945",
      "sort_order": 0,
      "created_at": "2025-11-19T...",
      "updated_at": "2025-11-19T..."
    }
  ],
  "total": 5
}
```

### Create Activity
```http
POST /api/v1/activities/
```

**Request Body:**
```json
{
  "trip_id": "uuid",
  "title": "Lunch at cafe",
  "description": "Try croissants",
  "scheduled_time": "2025-07-02T12:30:00",
  "category": "food",
  "latitude": "48.8566",
  "longitude": "2.3522"
}
```

**Categories:** `food`, `travel`, `stay`, `explore`

### Update Activity
```http
PATCH /api/v1/activities/{activity_id}
```

**Request Body (all fields optional):**
```json
{
  "title": "Updated title",
  "scheduled_time": "2025-07-02T13:00:00"
}
```

### Delete Activity
```http
DELETE /api/v1/activities/{activity_id}
```

**Response:** 204 No Content

### Reorder Activities (Drag & Drop)
```http
PUT /api/v1/activities/reorder?trip_id={trip_id}
```

**Request Body:**
```json
{
  "activity_orders": [
    {"id": "uuid-1", "sort_order": 0},
    {"id": "uuid-2", "sort_order": 1},
    {"id": "uuid-3", "sort_order": 2}
  ]
}
```

**Response:**
```json
{
  "message": "Activities reordered successfully"
}
```

---

## Memory Endpoints (Photo Locations)

### List Memories for Trip
```http
GET /api/v1/memories/?trip_id={trip_id}
```

**Query Parameters:**
- `trip_id` (required) - Trip UUID

**Response:**
```json
{
  "memories": [
    {
      "id": "uuid",
      "trip_id": "uuid",
      "photo_url": "https://cloudinary.com/...",
      "latitude": "48.8584",
      "longitude": "2.2945",
      "caption": "Beautiful view!",
      "taken_at": "2025-07-02T15:00:00",
      "created_at": "2025-11-19T..."
    }
  ],
  "total": 4
}
```

### Upload Memory with Photo
```http
POST /api/v1/memories/
```

**Content-Type:** `multipart/form-data`

**Form Data:**
- `trip_id` (required) - Trip UUID
- `latitude` (required) - GPS latitude
- `longitude` (required) - GPS longitude
- `caption` (optional) - Photo caption
- `taken_at` (optional) - When photo was taken
- `photo` (required) - Image file

**cURL Example:**
```bash
curl -X POST http://localhost:8546/api/v1/memories/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "trip_id=uuid" \
  -F "latitude=48.8584" \
  -F "longitude=2.2945" \
  -F "caption=Eiffel Tower view" \
  -F "taken_at=2025-07-02T15:00:00" \
  -F "photo=@/path/to/image.jpg"
```

### Delete Memory
```http
DELETE /api/v1/memories/{memory_id}
```

**Response:** 204 No Content

---

## Seed Data Endpoint

### Generate Demo Data
```http
POST /api/v1/seed/demo-data
```

**Description:** Creates 5 sample trips with 3-5 activities and 2-4 memories each

**Response:**
```json
{
  "message": "Demo data created successfully",
  "created_trips": [
    {"id": "uuid", "title": "Paris Adventure", "status": "planned"},
    ...
  ],
  "total_trips": 5,
  "total_activities": 20,
  "total_memories": 15
}
```

---

## Testing with cURL

### Full Flow Example

**1. Register:**
```bash
curl -X POST http://localhost:8546/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

**2. Save the token from response**

**3. Create a trip:**
```bash
curl -X POST http://localhost:8546/api/v1/trips/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tokyo Trip",
    "description": "Amazing journey",
    "start_date": "2025-06-01",
    "end_date": "2025-06-10",
    "status": "planned",
    "tags": ["japan", "culture"]
  }'
```

**4. Save the trip_id from response**

**5. Create an activity:**
```bash
curl -X POST http://localhost:8546/api/v1/activities/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "trip_id": "YOUR_TRIP_ID",
    "title": "Visit temple",
    "scheduled_time": "2025-06-02T10:00:00",
    "category": "explore",
    "latitude": "35.6762",
    "longitude": "139.6503"
  }'
```

**6. Or generate demo data:**
```bash
curl -X POST http://localhost:8546/api/v1/seed/demo-data \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Trip not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## API Documentation

**Swagger UI:** http://localhost:8546/docs
**ReDoc:** http://localhost:8546/redoc

The interactive Swagger UI allows you to test all endpoints directly in the browser!
