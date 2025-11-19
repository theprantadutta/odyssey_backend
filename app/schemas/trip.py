"""Trip schemas"""
from pydantic import BaseModel, UUID4
from datetime import date, datetime
from typing import Optional, List


class TripBase(BaseModel):
    """Base trip schema"""
    title: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    status: str = "planned"  # planned | ongoing | completed
    tags: Optional[List[str]] = []


class TripCreate(TripBase):
    """Trip creation request"""
    pass


class TripUpdate(BaseModel):
    """Trip update request (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class TripResponse(TripBase):
    """Trip response"""
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TripListResponse(BaseModel):
    """Paginated trip list response"""
    trips: List[TripResponse]
    total: int
    page: int
    page_size: int
