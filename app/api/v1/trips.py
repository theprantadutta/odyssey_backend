"""Trip endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.trip import TripCreate, TripUpdate, TripResponse, TripListResponse
from app.services.trip_service import TripService

router = APIRouter()


@router.get("/", response_model=TripListResponse)
async def list_trips(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all trips for authenticated user with pagination

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    """
    trip_service = TripService(db)

    skip = (page - 1) * page_size
    trips, total = trip_service.get_trips_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=page_size
    )

    return {
        "trips": trips,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new trip

    - **title**: Trip title (required)
    - **description**: Trip description
    - **cover_image_url**: URL to cover image (Cloudinary)
    - **start_date**: Trip start date
    - **end_date**: Trip end date
    - **status**: planned | ongoing | completed
    - **tags**: List of tags
    """
    trip_service = TripService(db)
    trip = trip_service.create_trip(current_user.id, trip_data)
    return trip


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trip by ID"""
    trip_service = TripService(db)
    trip = trip_service.get_trip_by_id(trip_id, current_user.id)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    return trip


@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: UUID,
    trip_data: TripUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update trip (all fields optional)"""
    trip_service = TripService(db)
    trip = trip_service.update_trip(trip_id, current_user.id, trip_data)

    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete trip (also deletes all associated activities and memories)"""
    trip_service = TripService(db)
    deleted = trip_service.delete_trip(trip_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )

    return None
