"""Packing Item model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class PackingItem(Base):
    """Packing item model for trip checklists"""

    __tablename__ = "packing_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, default="other")  # clothes | toiletries | electronics | documents | medicine | other
    is_packed = Column(Boolean, nullable=False, default=False)
    quantity = Column(Integer, nullable=False, default=1)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trip = relationship("Trip", back_populates="packing_items")

    def __repr__(self):
        return f"<PackingItem(id={self.id}, name={self.name}, is_packed={self.is_packed})>"
