"""Activity model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Activity(Base):
    """Activity model for itinerary items"""

    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)

    category = Column(String(50), nullable=False, default="explore")  # food | travel | stay | explore
    sort_order = Column(Integer, nullable=False, default=0)  # For drag-drop ordering

    latitude = Column(Numeric(precision=10, scale=8), nullable=True)
    longitude = Column(Numeric(precision=11, scale=8), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trip = relationship("Trip", back_populates="activities")

    def __repr__(self):
        return f"<Activity(id={self.id}, title={self.title}, category={self.category})>"
