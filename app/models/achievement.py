"""Achievement models for gamification."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Achievement(Base):
    """Predefined achievement definitions."""

    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Achievement identifier (unique key for programmatic access)
    type = Column(String(50), unique=True, nullable=False, index=True)

    # Display info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(50), nullable=False)  # Emoji or icon name

    # Category for grouping
    category = Column(String(50), nullable=False)  # trips, destinations, activities, social, etc.

    # Requirement to earn
    threshold = Column(Integer, nullable=False, default=1)

    # Rarity/tier
    tier = Column(String(20), nullable=False, default="bronze")  # bronze, silver, gold, platinum

    # Points awarded
    points = Column(Integer, nullable=False, default=10)

    # Is this achievement active?
    is_active = Column(Boolean, nullable=False, default=True)

    # Order for display
    sort_order = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    """User's earned achievements and progress."""

    __tablename__ = "user_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Progress towards achievement (for incremental achievements)
    progress = Column(Integer, nullable=False, default=0)

    # When the achievement was earned (null if not yet earned)
    earned_at = Column(DateTime, nullable=True)

    # Has user seen the notification?
    seen = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    @property
    def is_earned(self) -> bool:
        return self.earned_at is not None
