"""Memory service for photo location management"""
from sqlalchemy.orm import Session
from app.models.memory import Memory
from app.models.trip import Trip
from app.schemas.memory import MemoryCreate
from typing import Optional, List
from uuid import UUID


class MemoryService:
    """Service for memory (photo location) management"""

    def __init__(self, db: Session):
        self.db = db

    def get_memories_by_trip(
        self,
        trip_id: UUID,
        user_id: UUID
    ) -> tuple[List[Memory], int]:
        """
        Get all memories for a trip

        Returns:
            Tuple of (memories list, total count)
        """
        # First verify the trip belongs to the user
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return [], 0

        query = self.db.query(Memory).filter(Memory.trip_id == trip_id)
        total = query.count()
        memories = query.order_by(Memory.created_at.desc()).all()

        return memories, total

    def get_memory_by_id(
        self,
        memory_id: UUID,
        user_id: UUID
    ) -> Optional[Memory]:
        """Get a specific memory by ID (with user ownership check via trip)"""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()

        if not memory:
            return None

        # Verify ownership through trip
        trip = self.db.query(Trip).filter(
            Trip.id == memory.trip_id,
            Trip.user_id == user_id
        ).first()

        return memory if trip else None

    def create_memory(
        self,
        user_id: UUID,
        memory_data: MemoryCreate
    ) -> Optional[Memory]:
        """Create a new memory (photo location)"""
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == memory_data.trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return None

        db_memory = Memory(
            trip_id=memory_data.trip_id,
            photo_url=memory_data.photo_url,
            latitude=memory_data.latitude,
            longitude=memory_data.longitude,
            caption=memory_data.caption,
            taken_at=memory_data.taken_at
        )

        self.db.add(db_memory)
        self.db.commit()
        self.db.refresh(db_memory)

        return db_memory

    def delete_memory(self, memory_id: UUID, user_id: UUID) -> bool:
        """
        Delete a memory

        Returns:
            True if deleted, False if not found
        """
        memory = self.get_memory_by_id(memory_id, user_id)
        if not memory:
            return False

        self.db.delete(memory)
        self.db.commit()

        return True
