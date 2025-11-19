"""Trip service for CRUD operations"""
from sqlalchemy.orm import Session
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import TripCreate, TripUpdate
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class TripService:
    """Service for trip management"""

    def __init__(self, db: Session):
        self.db = db

    def get_trips_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Trip], int]:
        """
        Get all trips for a user with pagination

        Returns:
            Tuple of (trips list, total count)
        """
        query = self.db.query(Trip).filter(Trip.user_id == user_id)
        total = query.count()
        trips = query.order_by(Trip.created_at.desc()).offset(skip).limit(limit).all()
        return trips, total

    def get_trip_by_id(self, trip_id: UUID, user_id: UUID) -> Optional[Trip]:
        """Get a specific trip by ID (with user ownership check)"""
        return self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

    def create_trip(self, user_id: UUID, trip_data: TripCreate) -> Trip:
        """Create a new trip"""
        db_trip = Trip(
            user_id=user_id,
            title=trip_data.title,
            description=trip_data.description,
            cover_image_url=trip_data.cover_image_url,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            status=trip_data.status,
            tags=trip_data.tags or []
        )

        self.db.add(db_trip)
        self.db.commit()
        self.db.refresh(db_trip)

        return db_trip

    def update_trip(
        self,
        trip_id: UUID,
        user_id: UUID,
        trip_data: TripUpdate
    ) -> Optional[Trip]:
        """Update an existing trip"""
        trip = self.get_trip_by_id(trip_id, user_id)
        if not trip:
            return None

        # Update only provided fields
        update_data = trip_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(trip, field, value)

        trip.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(trip)

        return trip

    def delete_trip(self, trip_id: UUID, user_id: UUID) -> bool:
        """
        Delete a trip (and all associated activities and memories via cascade)

        Returns:
            True if deleted, False if not found
        """
        trip = self.get_trip_by_id(trip_id, user_id)
        if not trip:
            return False

        self.db.delete(trip)
        self.db.commit()

        return True
