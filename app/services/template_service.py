"""Template service for business logic"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from app.models.trip_template import TripTemplate
from app.models.trip import Trip
from app.models.activity import Activity
from app.models.packing_item import PackingItem
from app.schemas.template import (
    TripTemplateCreate,
    TripTemplateUpdate,
    TemplateFromTripCreate,
    TripFromTemplateCreate,
    TemplateStructure,
    ActivityTemplate,
    PackingItemTemplate,
)


class TemplateService:
    """Service for managing trip templates"""

    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self, user_id: UUID, template_data: TripTemplateCreate
    ) -> TripTemplate:
        """Create a new template"""
        template = TripTemplate(
            user_id=user_id,
            name=template_data.name,
            description=template_data.description,
            structure_json=template_data.structure_json.model_dump(),
            is_public=template_data.is_public,
            category=template_data.category.value if template_data.category else None,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def create_template_from_trip(
        self, user_id: UUID, data: TemplateFromTripCreate
    ) -> TripTemplate:
        """Create a template from an existing trip"""
        # Get the trip
        trip = self.db.query(Trip).filter(
            Trip.id == data.trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            raise ValueError("Trip not found or access denied")

        # Build the structure
        structure = TemplateStructure(
            duration_days=(trip.end_date - trip.start_date).days + 1 if trip.end_date else None,
            default_title=trip.title,
            default_description=trip.description,
            suggested_tags=trip.tags or [],
        )

        # Include activities if requested
        if data.include_activities:
            activities = self.db.query(Activity).filter(
                Activity.trip_id == data.trip_id
            ).order_by(Activity.sort_order).all()

            structure.activities = [
                ActivityTemplate(
                    title=act.title,
                    category=act.category,
                    description=act.description,
                    location=act.location,
                    notes=act.notes,
                )
                for act in activities
            ]

        # Include packing items if requested
        if data.include_packing_items:
            packing_items = self.db.query(PackingItem).filter(
                PackingItem.trip_id == data.trip_id
            ).order_by(PackingItem.sort_order).all()

            structure.packing_items = [
                PackingItemTemplate(
                    name=item.name,
                    category=item.category,
                    quantity=item.quantity,
                    notes=item.notes,
                )
                for item in packing_items
            ]

        # Create the template
        template = TripTemplate(
            user_id=user_id,
            name=data.name,
            description=data.description,
            structure_json=structure.model_dump(),
            is_public=data.is_public,
            category=data.category.value if data.category else None,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_template(self, template_id: UUID, user_id: UUID) -> Optional[TripTemplate]:
        """Get a template by ID (must be owned by user or public)"""
        return self.db.query(TripTemplate).filter(
            TripTemplate.id == template_id,
            or_(TripTemplate.user_id == user_id, TripTemplate.is_public == True)
        ).first()

    def get_user_templates(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
    ) -> tuple[List[TripTemplate], int]:
        """Get templates created by user"""
        query = self.db.query(TripTemplate).filter(TripTemplate.user_id == user_id)

        if category:
            query = query.filter(TripTemplate.category == category)

        total = query.count()
        templates = query.order_by(TripTemplate.created_at.desc()).offset(skip).limit(limit).all()

        return templates, total

    def get_public_templates(
        self,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[TripTemplate], int]:
        """Get public templates (template gallery)"""
        query = self.db.query(TripTemplate).filter(TripTemplate.is_public == True)

        if category:
            query = query.filter(TripTemplate.category == category)

        if search:
            query = query.filter(
                or_(
                    TripTemplate.name.ilike(f"%{search}%"),
                    TripTemplate.description.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        # Order by use count (popularity) and then by created_at
        templates = query.order_by(
            TripTemplate.use_count.desc(),
            TripTemplate.created_at.desc()
        ).offset(skip).limit(limit).all()

        return templates, total

    def update_template(
        self, template_id: UUID, user_id: UUID, update_data: TripTemplateUpdate
    ) -> Optional[TripTemplate]:
        """Update a template (must be owned by user)"""
        template = self.db.query(TripTemplate).filter(
            TripTemplate.id == template_id,
            TripTemplate.user_id == user_id
        ).first()

        if not template:
            return None

        if update_data.name is not None:
            template.name = update_data.name
        if update_data.description is not None:
            template.description = update_data.description
        if update_data.structure_json is not None:
            template.structure_json = update_data.structure_json.model_dump()
        if update_data.is_public is not None:
            template.is_public = update_data.is_public
        if update_data.category is not None:
            template.category = update_data.category.value

        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template_id: UUID, user_id: UUID) -> bool:
        """Delete a template (must be owned by user)"""
        template = self.db.query(TripTemplate).filter(
            TripTemplate.id == template_id,
            TripTemplate.user_id == user_id
        ).first()

        if not template:
            return False

        self.db.delete(template)
        self.db.commit()
        return True

    def create_trip_from_template(
        self, user_id: UUID, data: TripFromTemplateCreate
    ) -> Trip:
        """Create a new trip based on a template"""
        # Get the template
        template = self.db.query(TripTemplate).filter(
            TripTemplate.id == data.template_id,
            or_(TripTemplate.user_id == user_id, TripTemplate.is_public == True)
        ).first()

        if not template:
            raise ValueError("Template not found or access denied")

        structure = template.structure_json

        # Create the trip
        trip = Trip(
            user_id=user_id,
            title=data.title,
            description=data.description or structure.get("default_description"),
            start_date=datetime.strptime(data.start_date, "%Y-%m-%d").date(),
            end_date=datetime.strptime(data.end_date, "%Y-%m-%d").date() if data.end_date else None,
            tags=structure.get("suggested_tags", []),
            status="planned",
        )
        self.db.add(trip)
        self.db.flush()  # Get the trip ID

        # Create activities from template
        activities = structure.get("activities", [])
        for i, act_data in enumerate(activities):
            activity = Activity(
                trip_id=trip.id,
                title=act_data.get("title"),
                category=act_data.get("category", "explore"),
                description=act_data.get("description"),
                location=act_data.get("location"),
                notes=act_data.get("notes"),
                sort_order=i,
            )
            self.db.add(activity)

        # Create packing items from template
        packing_items = structure.get("packing_items", [])
        for i, item_data in enumerate(packing_items):
            item = PackingItem(
                trip_id=trip.id,
                name=item_data.get("name"),
                category=item_data.get("category", "other"),
                quantity=item_data.get("quantity", 1),
                notes=item_data.get("notes"),
                sort_order=i,
                is_packed=False,
            )
            self.db.add(item)

        # Increment the template use count
        template.use_count = (template.use_count or 0) + 1

        self.db.commit()
        self.db.refresh(trip)
        return trip
