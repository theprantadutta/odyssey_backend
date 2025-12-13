"""Sharing endpoints for trip collaboration"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.sharing import (
    TripShareCreate,
    TripShareUpdate,
    TripShareResponse,
    TripShareListResponse,
    InviteDetailsResponse,
    AcceptInviteResponse,
    SharedTripsResponse,
    SharePermission
)
from app.services.sharing_service import SharingService

router = APIRouter()


@router.post("/trips/{trip_id}/share", response_model=TripShareResponse, status_code=status.HTTP_201_CREATED)
async def share_trip(
    trip_id: UUID,
    share_data: TripShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share a trip with another user by email

    - **trip_id**: ID of the trip to share
    - **email**: Email of the person to share with
    - **permission**: Permission level (view or edit)
    """
    sharing_service = SharingService(db)
    share = sharing_service.share_trip(trip_id, current_user.id, share_data)

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return share


@router.get("/trips/{trip_id}/shares", response_model=TripShareListResponse)
async def list_trip_shares(
    trip_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all shares for a trip"""
    sharing_service = SharingService(db)
    shares, total = sharing_service.get_trip_shares(trip_id, current_user.id)

    return {
        "shares": shares,
        "total": total
    }


@router.patch("/trips/{trip_id}/shares/{share_id}", response_model=TripShareResponse)
async def update_share_permission(
    trip_id: UUID,
    share_id: UUID,
    update_data: TripShareUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update share permission level"""
    sharing_service = SharingService(db)
    share = sharing_service.update_share_permission(share_id, current_user.id, update_data)

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or unauthorized"
        )

    return share


@router.delete("/trips/{trip_id}/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    trip_id: UUID,
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a share (remove access)"""
    sharing_service = SharingService(db)
    revoked = sharing_service.revoke_share(share_id, current_user.id)

    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found or unauthorized"
        )

    return None


@router.get("/share/invite/{invite_code}", response_model=InviteDetailsResponse)
async def get_invite_details(
    invite_code: str,
    db: Session = Depends(get_db)
):
    """
    Get invite details by code (public endpoint)

    This endpoint doesn't require authentication so users can view
    invite details before logging in/registering.
    """
    sharing_service = SharingService(db)
    details = sharing_service.get_invite_details(invite_code)

    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found or expired"
        )

    return details


@router.post("/share/accept/{invite_code}", response_model=AcceptInviteResponse)
async def accept_invite(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a share invitation"""
    sharing_service = SharingService(db)
    share = sharing_service.accept_invite(invite_code, current_user.id)

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found, expired, or already processed"
        )

    return {
        "message": "Invitation accepted successfully",
        "trip_id": share.trip_id,
        "permission": share.permission
    }


@router.post("/share/decline/{invite_code}", status_code=status.HTTP_200_OK)
async def decline_invite(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Decline a share invitation"""
    sharing_service = SharingService(db)
    share = sharing_service.decline_invite(invite_code, current_user.id)

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )

    return {"message": "Invitation declined"}


@router.get("/trips/shared-with-me", response_model=SharedTripsResponse)
async def list_shared_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all trips that have been shared with the current user"""
    sharing_service = SharingService(db)
    trips, total = sharing_service.get_trips_shared_with_me(current_user.id)

    return {
        "trips": trips,
        "total": total
    }
