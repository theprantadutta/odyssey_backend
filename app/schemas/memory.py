"""Memory schemas"""
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class MemoryBase(BaseModel):
    """Base memory schema"""
    photo_url: str
    latitude: Decimal
    longitude: Decimal
    caption: Optional[str] = None
    taken_at: Optional[datetime] = None


class MemoryCreate(MemoryBase):
    """Memory creation request"""
    trip_id: UUID4


class MemoryResponse(MemoryBase):
    """Memory response"""
    id: UUID4
    trip_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryListResponse(BaseModel):
    """Memory list response"""
    memories: List[MemoryResponse]
    total: int
