"""Packing item schemas"""
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, List


class PackingItemBase(BaseModel):
    """Base packing item schema"""
    name: str
    category: str = "other"  # clothes | toiletries | electronics | documents | medicine | other
    is_packed: bool = False
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class PackingItemCreate(PackingItemBase):
    """Packing item creation request"""
    trip_id: UUID4


class PackingItemUpdate(BaseModel):
    """Packing item update request (all fields optional)"""
    name: Optional[str] = None
    category: Optional[str] = None
    is_packed: Optional[bool] = None
    quantity: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = None


class PackingItemResponse(PackingItemBase):
    """Packing item response"""
    id: UUID4
    trip_id: UUID4
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PackingItemReorderRequest(BaseModel):
    """Bulk reorder request"""
    item_orders: List[dict]  # [{"id": UUID, "sort_order": int}, ...]


class PackingListResponse(BaseModel):
    """Packing list response"""
    items: List[PackingItemResponse]
    total: int
    packed_count: int
    unpacked_count: int


class PackingProgressResponse(BaseModel):
    """Packing progress response"""
    total_items: int
    packed_items: int
    progress_percent: float
    by_category: List[dict]


class BulkToggleRequest(BaseModel):
    """Bulk toggle packed status"""
    item_ids: List[UUID4]
    is_packed: bool
