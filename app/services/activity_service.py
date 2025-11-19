"""Activity service for CRUD and reorder operations"""
from sqlalchemy.orm import Session
from app.models.activity import Activity
from app.models.trip import Trip
from app.schemas.activity import ActivityCreate, ActivityUpdate
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ActivityService:
    """Service for activity management"""

    def __init__(self, db: Session):
        self.db = db

    def get_activities_by_trip(
        self,
        trip_id: UUID,
        user_id: UUID
    ) -> tuple[List[Activity], int]:
        """
        Get all activities for a trip (sorted by sort_order)

        Returns:
            Tuple of (activities list, total count)
        """
        # First verify the trip belongs to the user
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return [], 0

        query = self.db.query(Activity).filter(Activity.trip_id == trip_id)
        total = query.count()
        activities = query.order_by(Activity.sort_order.asc()).all()

        return activities, total

    def get_activity_by_id(
        self,
        activity_id: UUID,
        user_id: UUID
    ) -> Optional[Activity]:
        """Get a specific activity by ID (with user ownership check via trip)"""
        activity = self.db.query(Activity).filter(Activity.id == activity_id).first()

        if not activity:
            return None

        # Verify ownership through trip
        trip = self.db.query(Trip).filter(
            Trip.id == activity.trip_id,
            Trip.user_id == user_id
        ).first()

        return activity if trip else None

    def create_activity(
        self,
        user_id: UUID,
        activity_data: ActivityCreate
    ) -> Optional[Activity]:
        """Create a new activity"""
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == activity_data.trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return None

        # Get the next sort_order (max + 1)
        max_order = self.db.query(Activity).filter(
            Activity.trip_id == activity_data.trip_id
        ).count()

        db_activity = Activity(
            trip_id=activity_data.trip_id,
            title=activity_data.title,
            description=activity_data.description,
            scheduled_time=activity_data.scheduled_time,
            category=activity_data.category,
            latitude=activity_data.latitude,
            longitude=activity_data.longitude,
            sort_order=max_order  # Append to end
        )

        self.db.add(db_activity)
        self.db.commit()
        self.db.refresh(db_activity)

        return db_activity

    def update_activity(
        self,
        activity_id: UUID,
        user_id: UUID,
        activity_data: ActivityUpdate
    ) -> Optional[Activity]:
        """Update an existing activity"""
        activity = self.get_activity_by_id(activity_id, user_id)
        if not activity:
            return None

        # Update only provided fields
        update_data = activity_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(activity, field, value)

        activity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(activity)

        return activity

    def delete_activity(self, activity_id: UUID, user_id: UUID) -> bool:
        """
        Delete an activity

        Returns:
            True if deleted, False if not found
        """
        activity = self.get_activity_by_id(activity_id, user_id)
        if not activity:
            return False

        self.db.delete(activity)
        self.db.commit()

        return True

    def reorder_activities(
        self,
        user_id: UUID,
        trip_id: UUID,
        activity_orders: List[dict]
    ) -> bool:
        """
        Bulk update activity sort orders (for drag-and-drop)

        Args:
            user_id: User ID for ownership verification
            trip_id: Trip ID to verify all activities belong to same trip
            activity_orders: List of {"id": UUID, "sort_order": int}

        Returns:
            True if successful, False if trip not found or unauthorized
        """
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return False

        # Update each activity's sort_order in a transaction
        try:
            for order_data in activity_orders:
                activity_id = UUID(order_data["id"])
                new_sort_order = order_data["sort_order"]

                activity = self.db.query(Activity).filter(
                    Activity.id == activity_id,
                    Activity.trip_id == trip_id
                ).first()

                if activity:
                    activity.sort_order = new_sort_order
                    activity.updated_at = datetime.utcnow()

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e
