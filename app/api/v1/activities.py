"""Activity endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.activity import (
    ActivityCreate,
    ActivityUpdate,
    ActivityResponse,
    ActivityListResponse,
    ActivityReorderRequest
)
from app.services.activity_service import ActivityService

router = APIRouter()


@router.get("/", response_model=ActivityListResponse)
async def list_activities(
    trip_id: UUID = Query(..., description="Trip ID to get activities for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all activities for a specific trip (sorted by sort_order)

    - **trip_id**: Required trip ID
    """
    activity_service = ActivityService(db)
    activities, total = activity_service.get_activities_by_trip(
        trip_id=trip_id,
        user_id=current_user.id
    )

    return {
        "activities": activities,
        "total": total
    }


@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new activity

    - **trip_id**: ID of the trip this activity belongs to
    - **title**: Activity title (required)
    - **description**: Activity description
    - **scheduled_time**: When the activity is scheduled
    - **category**: food | travel | stay | explore
    - **latitude**: GPS latitude (optional)
    - **longitude**: GPS longitude (optional)
    """
    activity_service = ActivityService(db)
    activity = activity_service.create_activity(current_user.id, activity_data)

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return activity


@router.patch("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: UUID,
    activity_data: ActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update activity (all fields optional)"""
    activity_service = ActivityService(db)
    activity = activity_service.update_activity(
        activity_id,
        current_user.id,
        activity_data
    )

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete activity"""
    activity_service = ActivityService(db)
    deleted = activity_service.delete_activity(activity_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    return None


@router.put("/reorder", status_code=status.HTTP_200_OK)
async def reorder_activities(
    trip_id: UUID = Query(..., description="Trip ID"),
    reorder_data: ActivityReorderRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk reorder activities (for drag-and-drop)

    - **trip_id**: Trip ID (query parameter)
    - **activity_orders**: List of {id: UUID, sort_order: int} (request body)

    Example request body:
    ```json
    {
      "activity_orders": [
        {"id": "uuid-1", "sort_order": 0},
        {"id": "uuid-2", "sort_order": 1},
        {"id": "uuid-3", "sort_order": 2}
      ]
    }
    ```
    """
    activity_service = ActivityService(db)
    success = activity_service.reorder_activities(
        user_id=current_user.id,
        trip_id=trip_id,
        activity_orders=reorder_data.activity_orders
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return {"message": "Activities reordered successfully"}
