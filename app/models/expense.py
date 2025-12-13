"""Expense model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Expense(Base):
    """Expense model for budget tracking"""

    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")  # ISO 4217 currency code

    category = Column(String(50), nullable=False, default="other")  # food | transport | accommodation | activities | shopping | other
    date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trip = relationship("Trip", back_populates="expenses")

    def __repr__(self):
        return f"<Expense(id={self.id}, title={self.title}, amount={self.amount} {self.currency})>"
