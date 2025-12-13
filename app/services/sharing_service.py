"""Sharing service for trip collaboration"""
from sqlalchemy.orm import Session
from app.models.trip_share import TripShare
from app.models.trip import Trip
from app.models.user import User
from app.schemas.sharing import TripShareCreate, TripShareUpdate, SharePermission, ShareStatus
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class SharingService:
    """Service for trip sharing and collaboration"""

    def __init__(self, db: Session):
        self.db = db

    def share_trip(
        self,
        trip_id: UUID,
        owner_id: UUID,
        share_data: TripShareCreate
    ) -> Optional[TripShare]:
        """
        Share a trip with another user by email

        Returns:
            TripShare if successful, None if trip not found or not owned
        """
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == owner_id
        ).first()

        if not trip:
            return None

        # Check if already shared with this email
        existing = self.db.query(TripShare).filter(
            TripShare.trip_id == trip_id,
            TripShare.shared_with_email == share_data.email
        ).first()

        if existing:
            # Update existing share
            existing.permission = share_data.permission.value
            existing.status = ShareStatus.pending.value
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # Check if user with this email exists
        shared_user = self.db.query(User).filter(
            User.email == share_data.email
        ).first()

        # Create new share
        db_share = TripShare(
            trip_id=trip_id,
            owner_id=owner_id,
            shared_with_email=share_data.email,
            shared_with_user_id=shared_user.id if shared_user else None,
            permission=share_data.permission.value
        )

        self.db.add(db_share)
        self.db.commit()
        self.db.refresh(db_share)

        return db_share

    def get_trip_shares(
        self,
        trip_id: UUID,
        owner_id: UUID
    ) -> tuple[List[TripShare], int]:
        """
        Get all shares for a trip

        Returns:
            Tuple of (shares list, total count)
        """
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == owner_id
        ).first()

        if not trip:
            return [], 0

        shares = self.db.query(TripShare).filter(
            TripShare.trip_id == trip_id
        ).order_by(TripShare.created_at.desc()).all()

        return shares, len(shares)

    def get_share_by_id(
        self,
        share_id: UUID,
        owner_id: UUID
    ) -> Optional[TripShare]:
        """Get a specific share by ID"""
        share = self.db.query(TripShare).filter(
            TripShare.id == share_id,
            TripShare.owner_id == owner_id
        ).first()

        return share

    def update_share_permission(
        self,
        share_id: UUID,
        owner_id: UUID,
        update_data: TripShareUpdate
    ) -> Optional[TripShare]:
        """Update share permission"""
        share = self.get_share_by_id(share_id, owner_id)
        if not share:
            return None

        if update_data.permission:
            share.permission = update_data.permission.value

        self.db.commit()
        self.db.refresh(share)

        return share

    def revoke_share(
        self,
        share_id: UUID,
        owner_id: UUID
    ) -> bool:
        """
        Revoke a share

        Returns:
            True if revoked, False if not found
        """
        share = self.get_share_by_id(share_id, owner_id)
        if not share:
            return False

        self.db.delete(share)
        self.db.commit()

        return True

    def get_invite_by_code(self, invite_code: str) -> Optional[TripShare]:
        """Get share details by invite code"""
        share = self.db.query(TripShare).filter(
            TripShare.invite_code == invite_code
        ).first()

        return share

    def get_invite_details(self, invite_code: str) -> Optional[dict]:
        """Get invite details for display (public)"""
        share = self.get_invite_by_code(invite_code)
        if not share:
            return None

        trip = self.db.query(Trip).filter(Trip.id == share.trip_id).first()
        owner = self.db.query(User).filter(User.id == share.owner_id).first()

        if not trip or not owner:
            return None

        return {
            "invite_code": share.invite_code,
            "trip_title": trip.title,
            "trip_cover_image": trip.cover_image_url,
            "owner_name": owner.name,
            "permission": share.permission,
            "status": share.status,
            "expires_at": share.invite_expires_at
        }

    def accept_invite(
        self,
        invite_code: str,
        user_id: UUID
    ) -> Optional[TripShare]:
        """
        Accept a share invitation

        Returns:
            Updated TripShare if successful, None otherwise
        """
        share = self.get_invite_by_code(invite_code)
        if not share:
            return None

        # Check if invite expired
        if share.invite_expires_at and share.invite_expires_at < datetime.utcnow():
            return None

        # Check if already accepted or declined
        if share.status != ShareStatus.pending.value:
            return share

        # Get user email
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Update share
        share.shared_with_user_id = user_id
        share.shared_with_email = user.email
        share.status = ShareStatus.accepted.value
        share.accepted_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(share)

        return share

    def decline_invite(
        self,
        invite_code: str,
        user_id: UUID
    ) -> Optional[TripShare]:
        """Decline a share invitation"""
        share = self.get_invite_by_code(invite_code)
        if not share:
            return None

        share.status = ShareStatus.declined.value

        self.db.commit()
        self.db.refresh(share)

        return share

    def get_trips_shared_with_me(
        self,
        user_id: UUID
    ) -> tuple[List[dict], int]:
        """
        Get all trips shared with the current user

        Returns:
            Tuple of (trips info list, total count)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return [], 0

        # Get shares by user ID or email
        shares = self.db.query(TripShare).filter(
            (TripShare.shared_with_user_id == user_id) |
            (TripShare.shared_with_email == user.email),
            TripShare.status == ShareStatus.accepted.value
        ).all()

        result = []
        for share in shares:
            trip = self.db.query(Trip).filter(Trip.id == share.trip_id).first()
            owner = self.db.query(User).filter(User.id == share.owner_id).first()

            if trip and owner:
                result.append({
                    "share_id": share.id,
                    "trip_id": trip.id,
                    "trip_title": trip.title,
                    "trip_cover_image": trip.cover_image_url,
                    "start_date": str(trip.start_date),
                    "end_date": str(trip.end_date),
                    "status": trip.status,
                    "owner_name": owner.name,
                    "owner_email": owner.email,
                    "permission": share.permission,
                    "shared_at": share.created_at
                })

        return result, len(result)

    def can_access_trip(
        self,
        trip_id: UUID,
        user_id: UUID,
        required_permission: str = "view"
    ) -> bool:
        """
        Check if user has access to a trip

        Returns:
            True if user owns trip or has been shared the trip
        """
        # Check if owner
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if trip:
            return True

        # Check if shared
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        share = self.db.query(TripShare).filter(
            TripShare.trip_id == trip_id,
            (TripShare.shared_with_user_id == user_id) |
            (TripShare.shared_with_email == user.email),
            TripShare.status == ShareStatus.accepted.value
        ).first()

        if not share:
            return False

        # Check permission level
        if required_permission == "edit" and share.permission != "edit":
            return False

        return True
