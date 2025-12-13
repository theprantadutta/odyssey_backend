"""Document model for trip-related document storage"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    """Document model for storing trip-related documents (tickets, reservations, etc.)"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type = Column(String(50), nullable=False, default="other")
    name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False, default="other")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    trip = relationship("Trip", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.name} ({self.type})>"
