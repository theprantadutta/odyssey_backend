"""Memory model (photo locations)"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Memory(Base):
    """Memory model for photo locations"""

    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)

    photo_url = Column(String(500), nullable=False)  # Cloudinary URL
    latitude = Column(Numeric(precision=10, scale=8), nullable=False)
    longitude = Column(Numeric(precision=11, scale=8), nullable=False)

    caption = Column(Text, nullable=True)
    taken_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="memories")

    def __repr__(self):
        return f"<Memory(id={self.id}, trip_id={self.trip_id})>"
