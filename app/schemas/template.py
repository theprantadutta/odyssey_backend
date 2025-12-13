"""Pydantic schemas for trip templates"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class TemplateCategory(str, Enum):
    """Template category options"""
    BEACH = "beach"
    ADVENTURE = "adventure"
    CITY = "city"
    CULTURAL = "cultural"
    ROAD_TRIP = "road_trip"
    BACKPACKING = "backpacking"
    LUXURY = "luxury"
    FAMILY = "family"
    BUSINESS = "business"
    OTHER = "other"


class ActivityTemplate(BaseModel):
    """Activity structure within a template"""
    title: str
    category: str
    description: Optional[str] = None
    location: Optional[str] = None
    estimated_duration_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    notes: Optional[str] = None


class PackingItemTemplate(BaseModel):
    """Packing item structure within a template"""
    name: str
    category: str
    quantity: int = 1
    notes: Optional[str] = None


class TemplateStructure(BaseModel):
    """Structure of a trip template"""
    duration_days: Optional[int] = None
    default_title: Optional[str] = None
    default_description: Optional[str] = None
    suggested_tags: List[str] = []
    activities: List[ActivityTemplate] = []
    packing_items: List[PackingItemTemplate] = []
    budget_categories: List[str] = []
    tips: List[str] = []


class TripTemplateCreate(BaseModel):
    """Schema for creating a template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    structure_json: TemplateStructure = Field(default_factory=TemplateStructure)
    is_public: bool = False
    category: Optional[TemplateCategory] = None


class TripTemplateUpdate(BaseModel):
    """Schema for updating a template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    structure_json: Optional[TemplateStructure] = None
    is_public: Optional[bool] = None
    category: Optional[TemplateCategory] = None


class TripTemplateResponse(BaseModel):
    """Schema for template response"""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    structure_json: dict
    is_public: bool
    category: Optional[str]
    use_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TripTemplateListResponse(BaseModel):
    """Schema for list of templates"""
    templates: List[TripTemplateResponse]
    total: int


class TemplateFromTripCreate(BaseModel):
    """Schema for creating a template from an existing trip"""
    trip_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False
    category: Optional[TemplateCategory] = None
    include_activities: bool = True
    include_packing_items: bool = True


class TripFromTemplateCreate(BaseModel):
    """Schema for creating a trip from a template"""
    template_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    start_date: str  # ISO date string
    end_date: Optional[str] = None  # ISO date string
    description: Optional[str] = None
