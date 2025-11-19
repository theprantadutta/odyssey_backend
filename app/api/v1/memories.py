"""Memory endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.cloudinary import upload_image
from app.models.user import User
from app.schemas.memory import MemoryCreate, MemoryResponse, MemoryListResponse
from app.services.memory_service import MemoryService

router = APIRouter()


@router.get("/", response_model=MemoryListResponse)
async def list_memories(
    trip_id: UUID = Query(..., description="Trip ID to get memories for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all memories for a specific trip

    - **trip_id**: Required trip ID
    """
    memory_service = MemoryService(db)
    memories, total = memory_service.get_memories_by_trip(
        trip_id=trip_id,
        user_id=current_user.id
    )

    return {
        "memories": memories,
        "total": total
    }


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    trip_id: UUID = Form(..., description="Trip ID"),
    latitude: Decimal = Form(..., description="GPS latitude"),
    longitude: Decimal = Form(..., description="GPS longitude"),
    caption: Optional[str] = Form(None, description="Photo caption"),
    taken_at: Optional[datetime] = Form(None, description="When photo was taken"),
    photo: UploadFile = File(..., description="Photo file"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new memory with photo upload

    - **trip_id**: ID of the trip
    - **latitude**: GPS latitude (required)
    - **longitude**: GPS longitude (required)
    - **caption**: Photo caption (optional)
    - **taken_at**: When photo was taken (optional)
    - **photo**: Photo file (required)

    **Note:** Photo is uploaded to Cloudinary
    """
    # Read photo file content
    photo_content = await photo.read()

    # Upload to Cloudinary
    try:
        public_id = f"odyssey/memories/{uuid4()}"
        photo_url = upload_image(photo_content, folder="odyssey/memories", public_id=public_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Photo upload failed: {str(e)}"
        )

    # Create memory
    memory_data = MemoryCreate(
        trip_id=trip_id,
        photo_url=photo_url,
        latitude=latitude,
        longitude=longitude,
        caption=caption,
        taken_at=taken_at
    )

    memory_service = MemoryService(db)
    memory = memory_service.create_memory(current_user.id, memory_data)

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return memory


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete memory"""
    memory_service = MemoryService(db)
    deleted = memory_service.delete_memory(memory_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    return None
