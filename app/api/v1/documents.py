"""Document endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
import cloudinary.uploader
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentsByType,
    DocumentType,
    FileType
)
from app.services.document_service import DocumentService

router = APIRouter()


def get_file_type(content_type: str) -> FileType:
    """Determine file type from content type"""
    if content_type == "application/pdf":
        return FileType.pdf
    elif content_type.startswith("image/"):
        return FileType.image
    return FileType.other


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    trip_id: UUID = Query(..., description="Trip ID to get documents for"),
    type: Optional[str] = Query(None, description="Filter by document type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents for a specific trip

    - **trip_id**: Required trip ID
    - **type**: Optional document type filter (ticket | reservation | passport | visa | insurance | itinerary | other)
    """
    document_service = DocumentService(db)
    documents, total = document_service.get_documents_by_trip(
        trip_id=trip_id,
        user_id=current_user.id,
        doc_type=type
    )

    return {
        "documents": documents,
        "total": total
    }


@router.get("/grouped", response_model=list[DocumentsByType])
async def list_documents_grouped(
    trip_id: UUID = Query(..., description="Trip ID to get documents for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get documents grouped by type for a trip

    Returns documents organized by type (tickets, reservations, etc.)
    """
    document_service = DocumentService(db)
    grouped = document_service.get_documents_grouped_by_type(
        trip_id=trip_id,
        user_id=current_user.id
    )

    return grouped


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific document by ID"""
    document_service = DocumentService(db)
    document = document_service.get_document_by_id(document_id, current_user.id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new document with a pre-uploaded file URL

    - **trip_id**: ID of the trip this document belongs to
    - **type**: Document type (ticket | reservation | passport | visa | insurance | itinerary | other)
    - **name**: Document name (required)
    - **file_url**: URL of the uploaded file (required)
    - **file_type**: File type (pdf | image | other)
    - **notes**: Additional notes (optional)
    """
    document_service = DocumentService(db)
    document = document_service.create_document(current_user.id, document_data)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return document


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    trip_id: UUID = Form(...),
    type: DocumentType = Form(default=DocumentType.other),
    name: str = Form(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document file directly

    - **file**: The file to upload (PDF or image)
    - **trip_id**: ID of the trip this document belongs to
    - **type**: Document type (ticket | reservation | passport | visa | insurance | itinerary | other)
    - **name**: Document name (required)
    - **notes**: Additional notes (optional)
    """
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: PDF, JPEG, PNG, WebP, GIF"
        )

    # Upload to Cloudinary
    try:
        # Determine resource type
        resource_type = "raw" if file.content_type == "application/pdf" else "image"

        result = cloudinary.uploader.upload(
            file.file,
            folder=f"odyssey/documents/{trip_id}",
            resource_type=resource_type,
            public_id=f"{name.replace(' ', '_')}_{file.filename}"
        )
        file_url = result["secure_url"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # Create document record
    document_data = DocumentCreate(
        trip_id=trip_id,
        type=type,
        name=name,
        file_url=file_url,
        file_type=get_file_type(file.content_type),
        notes=notes
    )

    document_service = DocumentService(db)
    document = document_service.create_document(current_user.id, document_data)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update document metadata (all fields optional)"""
    document_service = DocumentService(db)
    document = document_service.update_document(
        document_id,
        current_user.id,
        document_data
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document_service = DocumentService(db)
    deleted = document_service.delete_document(document_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return None
