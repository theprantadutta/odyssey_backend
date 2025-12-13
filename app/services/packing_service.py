"""Packing service for CRUD operations and progress tracking"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.packing_item import PackingItem
from app.models.trip import Trip
from app.schemas.packing import PackingItemCreate, PackingItemUpdate
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class PackingService:
    """Service for packing list management"""

    def __init__(self, db: Session):
        self.db = db

    def get_packing_items_by_trip(
        self,
        trip_id: UUID,
        user_id: UUID,
        category: Optional[str] = None
    ) -> tuple[List[PackingItem], int, int, int]:
        """
        Get all packing items for a trip (sorted by category then sort_order)

        Returns:
            Tuple of (items list, total count, packed count, unpacked count)
        """
        # First verify the trip belongs to the user
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return [], 0, 0, 0

        query = self.db.query(PackingItem).filter(PackingItem.trip_id == trip_id)

        # Filter by category if provided
        if category:
            query = query.filter(PackingItem.category == category)

        total = query.count()
        packed_count = query.filter(PackingItem.is_packed == True).count()
        unpacked_count = total - packed_count

        items = query.order_by(
            PackingItem.category.asc(),
            PackingItem.sort_order.asc()
        ).all()

        return items, total, packed_count, unpacked_count

    def get_packing_item_by_id(
        self,
        item_id: UUID,
        user_id: UUID
    ) -> Optional[PackingItem]:
        """Get a specific packing item by ID (with user ownership check via trip)"""
        item = self.db.query(PackingItem).filter(PackingItem.id == item_id).first()

        if not item:
            return None

        # Verify ownership through trip
        trip = self.db.query(Trip).filter(
            Trip.id == item.trip_id,
            Trip.user_id == user_id
        ).first()

        return item if trip else None

    def create_packing_item(
        self,
        user_id: UUID,
        item_data: PackingItemCreate
    ) -> Optional[PackingItem]:
        """Create a new packing item"""
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == item_data.trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return None

        # Get the next sort_order for this category
        max_order = self.db.query(PackingItem).filter(
            PackingItem.trip_id == item_data.trip_id,
            PackingItem.category == item_data.category
        ).count()

        db_item = PackingItem(
            trip_id=item_data.trip_id,
            name=item_data.name,
            category=item_data.category,
            is_packed=item_data.is_packed,
            quantity=item_data.quantity,
            notes=item_data.notes,
            sort_order=max_order
        )

        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)

        return db_item

    def update_packing_item(
        self,
        item_id: UUID,
        user_id: UUID,
        item_data: PackingItemUpdate
    ) -> Optional[PackingItem]:
        """Update an existing packing item"""
        item = self.get_packing_item_by_id(item_id, user_id)
        if not item:
            return None

        # Update only provided fields
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)

        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)

        return item

    def toggle_packed_status(
        self,
        item_id: UUID,
        user_id: UUID
    ) -> Optional[PackingItem]:
        """Toggle the packed status of an item"""
        item = self.get_packing_item_by_id(item_id, user_id)
        if not item:
            return None

        item.is_packed = not item.is_packed
        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)

        return item

    def bulk_toggle_packed(
        self,
        user_id: UUID,
        trip_id: UUID,
        item_ids: List[UUID],
        is_packed: bool
    ) -> bool:
        """Bulk update packed status for multiple items"""
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return False

        try:
            self.db.query(PackingItem).filter(
                PackingItem.id.in_(item_ids),
                PackingItem.trip_id == trip_id
            ).update(
                {"is_packed": is_packed, "updated_at": datetime.utcnow()},
                synchronize_session=False
            )
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def delete_packing_item(self, item_id: UUID, user_id: UUID) -> bool:
        """
        Delete a packing item

        Returns:
            True if deleted, False if not found
        """
        item = self.get_packing_item_by_id(item_id, user_id)
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()

        return True

    def reorder_packing_items(
        self,
        user_id: UUID,
        trip_id: UUID,
        item_orders: List[dict]
    ) -> bool:
        """
        Bulk update packing item sort orders (for drag-and-drop)

        Args:
            user_id: User ID for ownership verification
            trip_id: Trip ID to verify all items belong to same trip
            item_orders: List of {"id": UUID, "sort_order": int}

        Returns:
            True if successful, False if trip not found or unauthorized
        """
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return False

        try:
            for order_data in item_orders:
                item_id = UUID(order_data["id"])
                new_sort_order = order_data["sort_order"]

                item = self.db.query(PackingItem).filter(
                    PackingItem.id == item_id,
                    PackingItem.trip_id == trip_id
                ).first()

                if item:
                    item.sort_order = new_sort_order
                    item.updated_at = datetime.utcnow()

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e

    def get_packing_progress(
        self,
        trip_id: UUID,
        user_id: UUID
    ) -> dict:
        """
        Get packing progress summary for a trip

        Returns:
            Dict with progress stats
        """
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return {
                "total_items": 0,
                "packed_items": 0,
                "progress_percent": 0.0,
                "by_category": []
            }

        # Get totals
        total_items = self.db.query(PackingItem).filter(
            PackingItem.trip_id == trip_id
        ).count()

        packed_items = self.db.query(PackingItem).filter(
            PackingItem.trip_id == trip_id,
            PackingItem.is_packed == True
        ).count()

        # Calculate progress
        progress_percent = (packed_items / total_items * 100) if total_items > 0 else 0.0

        # Get breakdown by category
        category_stats = self.db.query(
            PackingItem.category,
            func.count(PackingItem.id).label("total"),
            func.sum(func.cast(PackingItem.is_packed, Integer)).label("packed")
        ).filter(
            PackingItem.trip_id == trip_id
        ).group_by(
            PackingItem.category
        ).all()

        by_category = [
            {
                "category": row.category,
                "total": row.total,
                "packed": row.packed or 0,
                "progress_percent": ((row.packed or 0) / row.total * 100) if row.total > 0 else 0.0
            }
            for row in category_stats
        ]

        return {
            "total_items": total_items,
            "packed_items": packed_items,
            "progress_percent": round(progress_percent, 1),
            "by_category": by_category
        }
