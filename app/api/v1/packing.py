"""Packing endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.packing import (
    PackingItemCreate,
    PackingItemUpdate,
    PackingItemResponse,
    PackingListResponse,
    PackingItemReorderRequest,
    PackingProgressResponse,
    BulkToggleRequest
)
from app.services.packing_service import PackingService

router = APIRouter()


@router.get("/", response_model=PackingListResponse)
async def list_packing_items(
    trip_id: UUID = Query(..., description="Trip ID to get packing items for"),
    category: str = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all packing items for a specific trip (sorted by category then sort_order)

    - **trip_id**: Required trip ID
    - **category**: Optional category filter (clothes | toiletries | electronics | documents | medicine | other)
    """
    packing_service = PackingService(db)
    items, total, packed_count, unpacked_count = packing_service.get_packing_items_by_trip(
        trip_id=trip_id,
        user_id=current_user.id,
        category=category
    )

    return {
        "items": items,
        "total": total,
        "packed_count": packed_count,
        "unpacked_count": unpacked_count
    }


@router.get("/progress", response_model=PackingProgressResponse)
async def get_packing_progress(
    trip_id: UUID = Query(..., description="Trip ID to get packing progress for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get packing progress for a trip

    Returns:
    - **total_items**: Total number of items
    - **packed_items**: Number of packed items
    - **progress_percent**: Percentage complete
    - **by_category**: Progress breakdown by category
    """
    packing_service = PackingService(db)
    progress = packing_service.get_packing_progress(
        trip_id=trip_id,
        user_id=current_user.id
    )

    return progress


@router.get("/{item_id}", response_model=PackingItemResponse)
async def get_packing_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific packing item by ID"""
    packing_service = PackingService(db)
    item = packing_service.get_packing_item_by_id(item_id, current_user.id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Packing item not found"
        )

    return item


@router.post("/", response_model=PackingItemResponse, status_code=status.HTTP_201_CREATED)
async def create_packing_item(
    item_data: PackingItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new packing item

    - **trip_id**: ID of the trip this item belongs to
    - **name**: Item name (required)
    - **category**: clothes | toiletries | electronics | documents | medicine | other
    - **is_packed**: Whether item is packed (default: false)
    - **quantity**: Number of this item (default: 1)
    - **notes**: Additional notes (optional)
    """
    packing_service = PackingService(db)
    item = packing_service.create_packing_item(current_user.id, item_data)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return item


@router.patch("/{item_id}", response_model=PackingItemResponse)
async def update_packing_item(
    item_id: UUID,
    item_data: PackingItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update packing item (all fields optional)"""
    packing_service = PackingService(db)
    item = packing_service.update_packing_item(
        item_id,
        current_user.id,
        item_data
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Packing item not found"
        )

    return item


@router.post("/{item_id}/toggle", response_model=PackingItemResponse)
async def toggle_packed_status(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle the packed status of an item"""
    packing_service = PackingService(db)
    item = packing_service.toggle_packed_status(item_id, current_user.id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Packing item not found"
        )

    return item


@router.post("/bulk-toggle", status_code=status.HTTP_200_OK)
async def bulk_toggle_packed(
    trip_id: UUID = Query(..., description="Trip ID"),
    toggle_data: BulkToggleRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk toggle packed status for multiple items

    - **trip_id**: Trip ID (query parameter)
    - **item_ids**: List of item IDs to update
    - **is_packed**: New packed status for all items
    """
    packing_service = PackingService(db)
    success = packing_service.bulk_toggle_packed(
        user_id=current_user.id,
        trip_id=trip_id,
        item_ids=toggle_data.item_ids,
        is_packed=toggle_data.is_packed
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return {"message": "Items updated successfully"}


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_packing_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete packing item"""
    packing_service = PackingService(db)
    deleted = packing_service.delete_packing_item(item_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Packing item not found"
        )

    return None


@router.put("/reorder", status_code=status.HTTP_200_OK)
async def reorder_packing_items(
    trip_id: UUID = Query(..., description="Trip ID"),
    reorder_data: PackingItemReorderRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk reorder packing items (for drag-and-drop)

    - **trip_id**: Trip ID (query parameter)
    - **item_orders**: List of {id: UUID, sort_order: int} (request body)
    """
    packing_service = PackingService(db)
    success = packing_service.reorder_packing_items(
        user_id=current_user.id,
        trip_id=trip_id,
        item_orders=reorder_data.item_orders
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return {"message": "Items reordered successfully"}
