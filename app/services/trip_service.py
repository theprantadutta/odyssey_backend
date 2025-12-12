"""Trip service for CRUD operations"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, asc, desc
from app.models.trip import Trip
from app.models.user import User
from app.schemas.trip import TripCreate, TripUpdate, TripSearchParams, SortField, SortOrder
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date


class TripService:
    """Service for trip management"""

    def __init__(self, db: Session):
        self.db = db

    def get_trips_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search_params: Optional[TripSearchParams] = None
    ) -> tuple[List[Trip], int, dict]:
        """
        Get all trips for a user with pagination and optional filtering

        Args:
            user_id: User's UUID
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            search_params: Optional search and filter parameters

        Returns:
            Tuple of (trips list, total count, filters_applied dict)
        """
        query = self.db.query(Trip).filter(Trip.user_id == user_id)
        filters_applied = {}

        if search_params:
            # Search by title (case-insensitive partial match)
            if search_params.search:
                search_term = f"%{search_params.search.lower()}%"
                query = query.filter(func.lower(Trip.title).like(search_term))
                filters_applied["search"] = search_params.search

            # Filter by status(es)
            if search_params.status:
                status_values = [s.value for s in search_params.status]
                query = query.filter(Trip.status.in_(status_values))
                filters_applied["status"] = status_values

            # Filter by start date range
            if search_params.start_date_from:
                query = query.filter(Trip.start_date >= search_params.start_date_from)
                filters_applied["start_date_from"] = str(search_params.start_date_from)

            if search_params.start_date_to:
                query = query.filter(Trip.start_date <= search_params.start_date_to)
                filters_applied["start_date_to"] = str(search_params.start_date_to)

            # Filter by tags (trips containing ANY of the specified tags)
            if search_params.tags:
                tag_conditions = []
                for tag in search_params.tags:
                    tag_conditions.append(Trip.tags.contains([tag]))
                query = query.filter(or_(*tag_conditions))
                filters_applied["tags"] = search_params.tags

            # Sorting
            sort_column = getattr(Trip, search_params.sort_by.value)
            if search_params.sort_order == SortOrder.asc:
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))

            filters_applied["sort_by"] = search_params.sort_by.value
            filters_applied["sort_order"] = search_params.sort_order.value
        else:
            # Default sorting by created_at descending
            query = query.order_by(Trip.created_at.desc())

        total = query.count()
        trips = query.offset(skip).limit(limit).all()

        return trips, total, filters_applied if filters_applied else None

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

    def get_available_tags(self, user_id: UUID) -> List[str]:
        """
        Get all unique tags used across user's trips.
        Useful for tag autocomplete in the frontend.
        """
        trips = self.db.query(Trip.tags).filter(Trip.user_id == user_id).all()
        all_tags = set()
        for (tags,) in trips:
            if tags:
                all_tags.update(tags)
        return sorted(list(all_tags))

    def create_default_trips_for_user(self, user_id: UUID) -> List[Trip]:
        """
        Create default sample trips for a new user.
        Called after user registration to give them starter content.
        """
        from datetime import timedelta

        today = date.today()

        default_trips = [
            {
                "title": "Weekend in Paris",
                "description": "A romantic getaway exploring the City of Lights. Visit the Eiffel Tower, stroll along the Seine, and enjoy French cuisine.",
                "cover_image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800",
                "start_date": today + timedelta(days=30),
                "end_date": today + timedelta(days=33),
                "status": "planned",
                "tags": ["europe", "romantic", "city"]
            },
            {
                "title": "Tokyo Adventure",
                "description": "Immerse yourself in Japanese culture, from ancient temples to modern technology. Experience sushi, anime, and cherry blossoms.",
                "cover_image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800",
                "start_date": today + timedelta(days=60),
                "end_date": today + timedelta(days=70),
                "status": "planned",
                "tags": ["asia", "culture", "food"]
            },
            {
                "title": "Bali Wellness Retreat",
                "description": "Relax and rejuvenate in Bali's serene landscapes. Yoga sessions, spa treatments, and beautiful rice terraces await.",
                "cover_image_url": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800",
                "start_date": today - timedelta(days=14),
                "end_date": today - timedelta(days=7),
                "status": "completed",
                "tags": ["asia", "wellness", "beach"]
            },
            {
                "title": "New York City Exploration",
                "description": "The Big Apple awaits! Broadway shows, Central Park, amazing food, and the iconic skyline.",
                "cover_image_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800",
                "start_date": today,
                "end_date": today + timedelta(days=5),
                "status": "ongoing",
                "tags": ["usa", "city", "entertainment"]
            }
        ]

        created_trips = []
        for trip_data in default_trips:
            db_trip = Trip(
                user_id=user_id,
                title=trip_data["title"],
                description=trip_data["description"],
                cover_image_url=trip_data["cover_image_url"],
                start_date=trip_data["start_date"],
                end_date=trip_data["end_date"],
                status=trip_data["status"],
                tags=trip_data["tags"]
            )
            self.db.add(db_trip)
            created_trips.append(db_trip)

        self.db.commit()

        # Refresh all trips to get their IDs
        for trip in created_trips:
            self.db.refresh(trip)

        return created_trips
