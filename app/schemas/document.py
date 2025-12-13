"""Document schemas for API request/response"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DocumentType(str, Enum):
    """Document type enum"""
    ticket = "ticket"
    reservation = "reservation"
    passport = "passport"
    visa = "visa"
    insurance = "insurance"
    itinerary = "itinerary"
    other = "other"


class FileType(str, Enum):
    """File type enum"""
    pdf = "pdf"
    image = "image"
    other = "other"


class DocumentBase(BaseModel):
    """Base schema for document"""
    type: DocumentType = Field(default=DocumentType.other, description="Document type")
    name: str = Field(..., min_length=1, max_length=255, description="Document name")
    notes: Optional[str] = Field(None, description="Additional notes")


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    trip_id: UUID = Field(..., description="Trip ID this document belongs to")
    file_url: str = Field(..., description="URL of the uploaded file")
    file_type: FileType = Field(default=FileType.other, description="File type")


class DocumentUpdate(BaseModel):
    """Schema for updating a document (all fields optional)"""
    type: Optional[DocumentType] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: UUID
    trip_id: UUID
    file_url: str
    file_type: FileType
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for list of documents response"""
    documents: List[DocumentResponse]
    total: int


class DocumentsByType(BaseModel):
    """Schema for documents grouped by type"""
    type: DocumentType
    documents: List[DocumentResponse]
    count: int
