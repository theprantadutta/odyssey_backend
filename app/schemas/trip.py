"""Trip schemas"""
from pydantic import BaseModel, UUID4, Field
from datetime import date, datetime
from typing import Optional, List
from enum import Enum


class TripStatus(str, Enum):
    """Trip status enum"""
    planned = "planned"
    ongoing = "ongoing"
    completed = "completed"


class SortField(str, Enum):
    """Sortable fields for trips"""
    created_at = "created_at"
    start_date = "start_date"
    title = "title"
    updated_at = "updated_at"


class SortOrder(str, Enum):
    """Sort order"""
    asc = "asc"
    desc = "desc"


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


class TripSearchParams(BaseModel):
    """Search and filter parameters for trips"""
    search: Optional[str] = Field(
        None,
        description="Search term for title (partial match, case-insensitive)"
    )
    status: Optional[List[TripStatus]] = Field(
        None,
        description="Filter by status(es)"
    )
    start_date_from: Optional[date] = Field(
        None,
        description="Filter trips starting on or after this date"
    )
    start_date_to: Optional[date] = Field(
        None,
        description="Filter trips starting on or before this date"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags (trips containing ANY of these tags)"
    )
    sort_by: SortField = Field(
        SortField.created_at,
        description="Field to sort by"
    )
    sort_order: SortOrder = Field(
        SortOrder.desc,
        description="Sort order (asc or desc)"
    )


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
    filters_applied: Optional[dict] = None
