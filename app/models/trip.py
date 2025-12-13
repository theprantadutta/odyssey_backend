"""Trip model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Trip(Base):
    """Trip model for travel journeys"""

    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="planned")  # planned | ongoing | completed

    tags = Column(ARRAY(String), nullable=True, default=[])

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="trips")
    activities = relationship("Activity", back_populates="trip", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="trip", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    packing_items = relationship("PackingItem", back_populates="trip", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="trip", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trip(id={self.id}, title={self.title}, status={self.status})>"
