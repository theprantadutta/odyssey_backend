"""TripShare model for trip sharing and collaboration"""
import uuid
import secrets
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


def generate_invite_code():
    """Generate a unique 12-character invite code"""
    return secrets.token_urlsafe(9)  # 12 characters


class TripShare(Base):
    """Model for sharing trips with other users"""
    __tablename__ = "trip_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    shared_with_email = Column(String(255), nullable=False)
    shared_with_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    permission = Column(String(10), nullable=False, default="view")  # view | edit
    invite_code = Column(String(50), unique=True, nullable=False, default=generate_invite_code)
    invite_expires_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending | accepted | declined
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="shares")
    owner = relationship("User", foreign_keys=[owner_id], backref="shared_trips")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id], backref="received_shares")

    def __repr__(self):
        return f"<TripShare {self.trip_id} -> {self.shared_with_email} ({self.status})>"
