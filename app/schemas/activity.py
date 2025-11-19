"""Activity schemas"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class ActivityBase(BaseModel):
    """Base activity schema"""
    title: str
    description: Optional[str] = None
    scheduled_time: datetime
    category: str = "explore"  # food | travel | stay | explore
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class ActivityCreate(ActivityBase):
    """Activity creation request"""
    trip_id: UUID4


class ActivityUpdate(BaseModel):
    """Activity update request (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    category: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class ActivityResponse(ActivityBase):
    """Activity response"""
    id: UUID4
    trip_id: UUID4
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityReorderRequest(BaseModel):
    """Bulk reorder request"""
    activity_orders: List[dict]  # [{"id": UUID, "sort_order": int}, ...]


class ActivityListResponse(BaseModel):
    """Activity list response"""
    activities: List[ActivityResponse]
    total: int
