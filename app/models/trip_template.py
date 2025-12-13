"""Trip template model for saving reusable trip structures"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class TripTemplate(Base):
    """Trip template model for reusable trip structures"""

    __tablename__ = "trip_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # JSON structure containing trip details, activities, packing items, etc.
    structure_json = Column(JSONB, nullable=False, default={})

    # Public templates can be used by all users
    is_public = Column(Boolean, nullable=False, default=False)

    # Category for organizing templates (beach, adventure, city, etc.)
    category = Column(String(50), nullable=True)

    # Number of times this template has been used
    use_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="templates")

    def __repr__(self):
        return f"<TripTemplate(id={self.id}, name={self.name}, is_public={self.is_public})>"
