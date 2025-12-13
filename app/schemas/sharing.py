"""Sharing schemas for API request/response"""
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum


class SharePermission(str, Enum):
    """Permission level for shared trips"""
    view = "view"
    edit = "edit"


class ShareStatus(str, Enum):
    """Status of a share invitation"""
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class TripShareCreate(BaseModel):
    """Schema for creating a trip share"""
    email: EmailStr = Field(..., description="Email of the person to share with")
    permission: SharePermission = Field(
        default=SharePermission.view,
        description="Permission level (view or edit)"
    )


class TripShareUpdate(BaseModel):
    """Schema for updating a trip share"""
    permission: Optional[SharePermission] = None


class TripShareResponse(BaseModel):
    """Schema for trip share response"""
    id: UUID
    trip_id: UUID
    owner_id: UUID
    shared_with_email: str
    shared_with_user_id: Optional[UUID] = None
    permission: SharePermission
    invite_code: str
    invite_expires_at: Optional[datetime] = None
    status: ShareStatus
    created_at: datetime
    accepted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TripShareListResponse(BaseModel):
    """Schema for list of shares"""
    shares: List[TripShareResponse]
    total: int


class InviteDetailsResponse(BaseModel):
    """Schema for invite details (public endpoint)"""
    invite_code: str
    trip_title: str
    trip_cover_image: Optional[str] = None
    owner_name: str
    permission: SharePermission
    status: ShareStatus
    expires_at: Optional[datetime] = None


class AcceptInviteResponse(BaseModel):
    """Schema for accepting an invite"""
    message: str
    trip_id: UUID
    permission: SharePermission


class SharedTripInfo(BaseModel):
    """Schema for a trip that was shared with the user"""
    share_id: UUID
    trip_id: UUID
    trip_title: str
    trip_cover_image: Optional[str] = None
    start_date: str
    end_date: str
    status: str
    owner_name: str
    owner_email: str
    permission: SharePermission
    shared_at: datetime


class SharedTripsResponse(BaseModel):
    """Schema for list of trips shared with user"""
    trips: List[SharedTripInfo]
    total: int
