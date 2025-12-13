"""Trip template API routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.api.deps import get_current_user
from app.services.template_service import TemplateService
from app.schemas.template import (
    TripTemplateCreate,
    TripTemplateUpdate,
    TripTemplateResponse,
    TripTemplateListResponse,
    TemplateFromTripCreate,
    TripFromTemplateCreate,
    TemplateCategory,
)

router = APIRouter()


@router.post("/", response_model=TripTemplateResponse)
def create_template(
    template_data: TripTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new trip template"""
    service = TemplateService(db)
    template = service.create_template(current_user.id, template_data)
    return template


@router.post("/from-trip", response_model=TripTemplateResponse)
def create_template_from_trip(
    data: TemplateFromTripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a template from an existing trip"""
    service = TemplateService(db)
    try:
        template = service.create_template_from_trip(current_user.id, data)
        return template
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/use/{template_id}")
def create_trip_from_template(
    template_id: UUID,
    data: TripFromTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new trip from a template"""
    # Ensure template_id in path matches body
    if template_id != data.template_id:
        raise HTTPException(status_code=400, detail="Template ID mismatch")

    service = TemplateService(db)
    try:
        trip = service.create_trip_from_template(current_user.id, data)
        return {
            "message": "Trip created successfully",
            "trip_id": str(trip.id),
            "trip_title": trip.title,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=TripTemplateListResponse)
def get_my_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[TemplateCategory] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get templates created by the current user"""
    service = TemplateService(db)
    skip = (page - 1) * page_size
    templates, total = service.get_user_templates(
        current_user.id,
        skip=skip,
        limit=page_size,
        category=category.value if category else None,
    )
    return TripTemplateListResponse(templates=templates, total=total)


@router.get("/public", response_model=TripTemplateListResponse)
def get_public_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[TemplateCategory] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get public templates (template gallery)"""
    service = TemplateService(db)
    skip = (page - 1) * page_size
    templates, total = service.get_public_templates(
        skip=skip,
        limit=page_size,
        category=category.value if category else None,
        search=search,
    )
    return TripTemplateListResponse(templates=templates, total=total)


@router.get("/categories")
def get_template_categories():
    """Get available template categories"""
    return [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in TemplateCategory
    ]


@router.get("/{template_id}", response_model=TripTemplateResponse)
def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific template"""
    service = TemplateService(db)
    template = service.get_template(template_id, current_user.id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch("/{template_id}", response_model=TripTemplateResponse)
def update_template(
    template_id: UUID,
    update_data: TripTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a template (must be owner)"""
    service = TemplateService(db)
    template = service.update_template(template_id, current_user.id, update_data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found or access denied")
    return template


@router.delete("/{template_id}")
def delete_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a template (must be owner)"""
    service = TemplateService(db)
    success = service.delete_template(template_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found or access denied")
    return {"message": "Template deleted successfully"}
