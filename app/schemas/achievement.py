"""Achievement schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class AchievementBase(BaseModel):
    """Base achievement schema."""

    type: str
    name: str
    description: str
    icon: str
    category: str
    threshold: int = 1
    tier: str = "bronze"
    points: int = 10


class AchievementCreate(AchievementBase):
    """Schema for creating an achievement."""

    sort_order: int = 0


class AchievementResponse(AchievementBase):
    """Schema for achievement response."""

    id: UUID
    sort_order: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserAchievementBase(BaseModel):
    """Base user achievement schema."""

    progress: int = 0


class UserAchievementResponse(BaseModel):
    """Schema for user achievement response."""

    id: UUID
    user_id: UUID
    achievement_id: UUID
    progress: int
    earned_at: Optional[datetime] = None
    seen: bool
    created_at: datetime

    # Include achievement details
    achievement: AchievementResponse

    class Config:
        from_attributes = True


class AchievementProgressUpdate(BaseModel):
    """Schema for updating achievement progress."""

    progress: int = Field(..., ge=0)


class AchievementUnlockResponse(BaseModel):
    """Response when an achievement is unlocked."""

    achievement: AchievementResponse
    earned_at: datetime
    is_new: bool  # True if just unlocked


class UserAchievementsResponse(BaseModel):
    """Response for user's achievements."""

    earned: List[UserAchievementResponse]
    in_progress: List[UserAchievementResponse]
    locked: List[AchievementResponse]
    total_points: int
    earned_count: int
    total_count: int


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""

    user_id: UUID
    email: str
    total_points: int
    earned_count: int
    rank: int


class LeaderboardResponse(BaseModel):
    """Leaderboard response."""

    entries: List[LeaderboardEntry]
    user_rank: Optional[int] = None
    user_points: Optional[int] = None


# Predefined achievement types
ACHIEVEMENT_DEFINITIONS = [
    # Trip milestones
    {
        "type": "first_trip",
        "name": "First Steps",
        "description": "Create your first trip",
        "icon": "🎒",
        "category": "trips",
        "threshold": 1,
        "tier": "bronze",
        "points": 10,
    },
    {
        "type": "trips_5",
        "name": "Frequent Traveler",
        "description": "Create 5 trips",
        "icon": "✈️",
        "category": "trips",
        "threshold": 5,
        "tier": "silver",
        "points": 25,
    },
    {
        "type": "trips_10",
        "name": "Globetrotter",
        "description": "Create 10 trips",
        "icon": "🌍",
        "category": "trips",
        "threshold": 10,
        "tier": "gold",
        "points": 50,
    },
    {
        "type": "trips_25",
        "name": "World Explorer",
        "description": "Create 25 trips",
        "icon": "🗺️",
        "category": "trips",
        "threshold": 25,
        "tier": "platinum",
        "points": 100,
    },
    # Completed trips
    {
        "type": "first_completed",
        "name": "Journey Complete",
        "description": "Complete your first trip",
        "icon": "🏆",
        "category": "trips",
        "threshold": 1,
        "tier": "bronze",
        "points": 15,
    },
    {
        "type": "completed_5",
        "name": "Seasoned Traveler",
        "description": "Complete 5 trips",
        "icon": "⭐",
        "category": "trips",
        "threshold": 5,
        "tier": "silver",
        "points": 30,
    },
    {
        "type": "completed_10",
        "name": "Adventure Master",
        "description": "Complete 10 trips",
        "icon": "🌟",
        "category": "trips",
        "threshold": 10,
        "tier": "gold",
        "points": 60,
    },
    # Activities
    {
        "type": "first_activity",
        "name": "Activity Planner",
        "description": "Create your first activity",
        "icon": "📋",
        "category": "activities",
        "threshold": 1,
        "tier": "bronze",
        "points": 5,
    },
    {
        "type": "activities_25",
        "name": "Busy Bee",
        "description": "Create 25 activities",
        "icon": "🐝",
        "category": "activities",
        "threshold": 25,
        "tier": "silver",
        "points": 20,
    },
    {
        "type": "activities_100",
        "name": "Activity Master",
        "description": "Create 100 activities",
        "icon": "📊",
        "category": "activities",
        "threshold": 100,
        "tier": "gold",
        "points": 50,
    },
    # Memories
    {
        "type": "first_memory",
        "name": "Memory Maker",
        "description": "Upload your first photo",
        "icon": "📸",
        "category": "memories",
        "threshold": 1,
        "tier": "bronze",
        "points": 5,
    },
    {
        "type": "memories_50",
        "name": "Photo Enthusiast",
        "description": "Upload 50 photos",
        "icon": "🖼️",
        "category": "memories",
        "threshold": 50,
        "tier": "silver",
        "points": 25,
    },
    {
        "type": "memories_200",
        "name": "Memory Master",
        "description": "Upload 200 photos",
        "icon": "📷",
        "category": "memories",
        "threshold": 200,
        "tier": "gold",
        "points": 50,
    },
    # Packing
    {
        "type": "packing_complete",
        "name": "All Packed",
        "description": "Complete a packing list",
        "icon": "🧳",
        "category": "packing",
        "threshold": 1,
        "tier": "bronze",
        "points": 10,
    },
    {
        "type": "packing_10",
        "name": "Packing Pro",
        "description": "Complete 10 packing lists",
        "icon": "👜",
        "category": "packing",
        "threshold": 10,
        "tier": "silver",
        "points": 30,
    },
    # Social
    {
        "type": "first_share",
        "name": "Sharing is Caring",
        "description": "Share a trip with someone",
        "icon": "🤝",
        "category": "social",
        "threshold": 1,
        "tier": "bronze",
        "points": 10,
    },
    {
        "type": "shares_5",
        "name": "Social Butterfly",
        "description": "Share 5 trips",
        "icon": "🦋",
        "category": "social",
        "threshold": 5,
        "tier": "silver",
        "points": 25,
    },
    {
        "type": "first_template",
        "name": "Template Creator",
        "description": "Create your first template",
        "icon": "📝",
        "category": "social",
        "threshold": 1,
        "tier": "bronze",
        "points": 15,
    },
    {
        "type": "template_used",
        "name": "Trendsetter",
        "description": "Have your template used by someone",
        "icon": "🔥",
        "category": "social",
        "threshold": 1,
        "tier": "gold",
        "points": 50,
    },
    # Budget
    {
        "type": "first_expense",
        "name": "Budget Tracker",
        "description": "Track your first expense",
        "icon": "💰",
        "category": "budget",
        "threshold": 1,
        "tier": "bronze",
        "points": 5,
    },
    {
        "type": "expenses_50",
        "name": "Money Manager",
        "description": "Track 50 expenses",
        "icon": "💵",
        "category": "budget",
        "threshold": 50,
        "tier": "silver",
        "points": 25,
    },
    # Special
    {
        "type": "early_adopter",
        "name": "Early Adopter",
        "description": "Join Odyssey in its early days",
        "icon": "🚀",
        "category": "special",
        "threshold": 1,
        "tier": "gold",
        "points": 100,
    },
]
