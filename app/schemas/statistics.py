"""Statistics schemas."""
from datetime import date
from typing import Dict, List, Optional
from pydantic import BaseModel


class TripStatistics(BaseModel):
    """Trip-related statistics."""

    total_trips: int
    planned_trips: int
    ongoing_trips: int
    completed_trips: int
    trips_this_year: int
    trips_by_year: Dict[int, int]
    average_trip_duration: float


class DestinationStatistics(BaseModel):
    """Destination-related statistics."""

    countries_visited: int
    cities_visited: int
    top_destinations: List[str]


class ActivityStatistics(BaseModel):
    """Activity-related statistics."""

    total_activities: int
    completed_activities: int
    activities_by_category: Dict[str, int]


class MemoryStatistics(BaseModel):
    """Memory-related statistics."""

    total_memories: int
    memories_this_year: int
    memories_by_trip: Dict[str, int]  # trip_id -> count


class ExpenseStatistics(BaseModel):
    """Expense-related statistics."""

    total_expenses: int
    total_amount_by_currency: Dict[str, float]
    expenses_by_category: Dict[str, float]
    average_expense: float


class PackingStatistics(BaseModel):
    """Packing-related statistics."""

    total_packing_items: int
    packed_items: int
    packing_completion_rate: float


class SocialStatistics(BaseModel):
    """Social-related statistics."""

    trips_shared: int
    trips_shared_with_me: int
    templates_created: int
    templates_used_by_others: int


class OverallStatistics(BaseModel):
    """Overall user statistics."""

    trips: TripStatistics
    activities: ActivityStatistics
    memories: MemoryStatistics
    expenses: ExpenseStatistics
    packing: PackingStatistics
    social: SocialStatistics
    total_days_traveled: int
    member_since: date
    achievement_points: int


class YearInReviewStats(BaseModel):
    """Year in review statistics."""

    year: int
    total_trips: int
    total_days_traveled: int
    countries_visited: List[str]
    cities_visited: List[str]
    total_activities: int
    total_memories: int
    total_expenses_by_currency: Dict[str, float]
    top_destinations: List[str]
    longest_trip_days: int
    longest_trip_title: Optional[str]
    most_active_month: Optional[str]
    trips_by_month: Dict[str, int]
    achievements_earned: int
    new_achievement_points: int


class TravelTimelineItem(BaseModel):
    """Item for travel timeline."""

    trip_id: str
    title: str
    destination: Optional[str]
    start_date: date
    end_date: date
    status: str
    cover_image_url: Optional[str]
    activities_count: int
    memories_count: int


class TravelTimeline(BaseModel):
    """User's travel timeline."""

    items: List[TravelTimelineItem]
    total_trips: int
