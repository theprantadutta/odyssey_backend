"""Statistics service for user analytics."""
from datetime import date, datetime
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from collections import defaultdict

from app.models.user import User
from app.models.trip import Trip
from app.models.activity import Activity
from app.models.memory import Memory
from app.models.expense import Expense
from app.models.packing_item import PackingItem
from app.models.trip_share import TripShare
from app.models.trip_template import TripTemplate
from app.models.achievement import UserAchievement, Achievement
from app.schemas.statistics import (
    OverallStatistics,
    TripStatistics,
    ActivityStatistics,
    MemoryStatistics,
    ExpenseStatistics,
    PackingStatistics,
    SocialStatistics,
    YearInReviewStats,
    TravelTimeline,
    TravelTimelineItem,
)


class StatisticsService:
    """Service for user statistics."""

    def __init__(self, db: Session):
        self.db = db

    def get_overall_statistics(self, user_id: UUID) -> OverallStatistics:
        """Get comprehensive user statistics."""
        user = self.db.query(User).filter(User.id == user_id).first()

        trips = self._get_trip_statistics(user_id)
        activities = self._get_activity_statistics(user_id)
        memories = self._get_memory_statistics(user_id)
        expenses = self._get_expense_statistics(user_id)
        packing = self._get_packing_statistics(user_id)
        social = self._get_social_statistics(user_id)
        total_days = self._get_total_days_traveled(user_id)
        achievement_points = self._get_achievement_points(user_id)

        return OverallStatistics(
            trips=trips,
            activities=activities,
            memories=memories,
            expenses=expenses,
            packing=packing,
            social=social,
            total_days_traveled=total_days,
            member_since=user.created_at.date() if user else date.today(),
            achievement_points=achievement_points,
        )

    def get_year_in_review(
        self, user_id: UUID, year: Optional[int] = None
    ) -> YearInReviewStats:
        """Get year-in-review statistics."""
        if year is None:
            year = datetime.now().year

        # Get trips for the year
        trips = (
            self.db.query(Trip)
            .filter(
                and_(
                    Trip.user_id == user_id,
                    extract("year", Trip.start_date) == year,
                )
            )
            .all()
        )

        # Calculate stats
        total_trips = len(trips)
        total_days = sum(
            (
                datetime.strptime(t.end_date, "%Y-%m-%d")
                - datetime.strptime(t.start_date, "%Y-%m-%d")
            ).days
            + 1
            for t in trips
            if t.start_date and t.end_date
        )

        # Destinations (from trip destinations field)
        destinations = set()
        for trip in trips:
            if trip.destination:
                destinations.add(trip.destination)

        # Get activities count for year
        total_activities = (
            self.db.query(func.count(Activity.id))
            .join(Trip)
            .filter(
                and_(
                    Trip.user_id == user_id,
                    extract("year", Trip.start_date) == year,
                )
            )
            .scalar()
            or 0
        )

        # Get memories count for year
        total_memories = (
            self.db.query(func.count(Memory.id))
            .join(Trip)
            .filter(
                and_(
                    Trip.user_id == user_id,
                    extract("year", Trip.start_date) == year,
                )
            )
            .scalar()
            or 0
        )

        # Get expenses for year
        expenses = (
            self.db.query(Expense.currency, func.sum(Expense.amount))
            .join(Trip)
            .filter(
                and_(
                    Trip.user_id == user_id,
                    extract("year", Trip.start_date) == year,
                )
            )
            .group_by(Expense.currency)
            .all()
        )
        total_expenses_by_currency = {
            currency: float(amount) for currency, amount in expenses if currency
        }

        # Longest trip
        longest_trip = None
        longest_days = 0
        for trip in trips:
            if trip.start_date and trip.end_date:
                days = (
                    datetime.strptime(trip.end_date, "%Y-%m-%d")
                    - datetime.strptime(trip.start_date, "%Y-%m-%d")
                ).days + 1
                if days > longest_days:
                    longest_days = days
                    longest_trip = trip

        # Trips by month
        trips_by_month = defaultdict(int)
        for trip in trips:
            if trip.start_date:
                month = datetime.strptime(trip.start_date, "%Y-%m-%d").strftime("%B")
                trips_by_month[month] += 1

        # Most active month
        most_active_month = None
        if trips_by_month:
            most_active_month = max(trips_by_month, key=trips_by_month.get)

        # Achievements earned this year
        achievements_earned = (
            self.db.query(func.count(UserAchievement.id))
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.earned_at.isnot(None),
                    extract("year", UserAchievement.earned_at) == year,
                )
            )
            .scalar()
            or 0
        )

        # Points earned this year
        new_points = (
            self.db.query(func.sum(Achievement.points))
            .join(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.earned_at.isnot(None),
                    extract("year", UserAchievement.earned_at) == year,
                )
            )
            .scalar()
            or 0
        )

        return YearInReviewStats(
            year=year,
            total_trips=total_trips,
            total_days_traveled=total_days,
            countries_visited=[],  # Would need geocoding
            cities_visited=list(destinations),
            total_activities=total_activities,
            total_memories=total_memories,
            total_expenses_by_currency=total_expenses_by_currency,
            top_destinations=list(destinations)[:5],
            longest_trip_days=longest_days,
            longest_trip_title=longest_trip.title if longest_trip else None,
            most_active_month=most_active_month,
            trips_by_month=dict(trips_by_month),
            achievements_earned=achievements_earned,
            new_achievement_points=new_points,
        )

    def get_travel_timeline(
        self, user_id: UUID, limit: int = 20, offset: int = 0
    ) -> TravelTimeline:
        """Get user's travel timeline."""
        trips = (
            self.db.query(Trip)
            .filter(Trip.user_id == user_id)
            .order_by(Trip.start_date.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        total = (
            self.db.query(func.count(Trip.id))
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        items = []
        for trip in trips:
            activities_count = (
                self.db.query(func.count(Activity.id))
                .filter(Activity.trip_id == trip.id)
                .scalar()
                or 0
            )
            memories_count = (
                self.db.query(func.count(Memory.id))
                .filter(Memory.trip_id == trip.id)
                .scalar()
                or 0
            )

            items.append(
                TravelTimelineItem(
                    trip_id=str(trip.id),
                    title=trip.title,
                    destination=trip.destination,
                    start_date=datetime.strptime(trip.start_date, "%Y-%m-%d").date(),
                    end_date=datetime.strptime(trip.end_date, "%Y-%m-%d").date(),
                    status=trip.status,
                    cover_image_url=trip.cover_image_url,
                    activities_count=activities_count,
                    memories_count=memories_count,
                )
            )

        return TravelTimeline(items=items, total_trips=total)

    def _get_trip_statistics(self, user_id: UUID) -> TripStatistics:
        """Get trip statistics."""
        current_year = datetime.now().year

        total = (
            self.db.query(func.count(Trip.id))
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        planned = (
            self.db.query(func.count(Trip.id))
            .filter(and_(Trip.user_id == user_id, Trip.status == "planned"))
            .scalar()
            or 0
        )

        ongoing = (
            self.db.query(func.count(Trip.id))
            .filter(and_(Trip.user_id == user_id, Trip.status == "ongoing"))
            .scalar()
            or 0
        )

        completed = (
            self.db.query(func.count(Trip.id))
            .filter(and_(Trip.user_id == user_id, Trip.status == "completed"))
            .scalar()
            or 0
        )

        this_year = (
            self.db.query(func.count(Trip.id))
            .filter(
                and_(
                    Trip.user_id == user_id,
                    extract("year", Trip.start_date) == current_year,
                )
            )
            .scalar()
            or 0
        )

        # Trips by year
        trips_by_year_result = (
            self.db.query(
                extract("year", Trip.start_date).label("year"),
                func.count(Trip.id),
            )
            .filter(Trip.user_id == user_id)
            .group_by("year")
            .all()
        )
        trips_by_year = {int(year): count for year, count in trips_by_year_result if year}

        # Average duration
        trips = self.db.query(Trip).filter(Trip.user_id == user_id).all()
        total_days = 0
        trip_count = 0
        for trip in trips:
            if trip.start_date and trip.end_date:
                days = (
                    datetime.strptime(trip.end_date, "%Y-%m-%d")
                    - datetime.strptime(trip.start_date, "%Y-%m-%d")
                ).days + 1
                total_days += days
                trip_count += 1

        avg_duration = total_days / trip_count if trip_count > 0 else 0

        return TripStatistics(
            total_trips=total,
            planned_trips=planned,
            ongoing_trips=ongoing,
            completed_trips=completed,
            trips_this_year=this_year,
            trips_by_year=trips_by_year,
            average_trip_duration=round(avg_duration, 1),
        )

    def _get_activity_statistics(self, user_id: UUID) -> ActivityStatistics:
        """Get activity statistics."""
        total = (
            self.db.query(func.count(Activity.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        completed = (
            self.db.query(func.count(Activity.id))
            .join(Trip)
            .filter(and_(Trip.user_id == user_id, Activity.is_completed == True))
            .scalar()
            or 0
        )

        by_category = (
            self.db.query(Activity.category, func.count(Activity.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .group_by(Activity.category)
            .all()
        )
        activities_by_category = {cat: count for cat, count in by_category if cat}

        return ActivityStatistics(
            total_activities=total,
            completed_activities=completed,
            activities_by_category=activities_by_category,
        )

    def _get_memory_statistics(self, user_id: UUID) -> MemoryStatistics:
        """Get memory statistics."""
        current_year = datetime.now().year

        total = (
            self.db.query(func.count(Memory.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        this_year = (
            self.db.query(func.count(Memory.id))
            .join(Trip)
            .filter(
                and_(
                    Trip.user_id == user_id,
                    extract("year", Memory.created_at) == current_year,
                )
            )
            .scalar()
            or 0
        )

        by_trip = (
            self.db.query(Trip.id, func.count(Memory.id))
            .join(Memory)
            .filter(Trip.user_id == user_id)
            .group_by(Trip.id)
            .all()
        )
        memories_by_trip = {str(trip_id): count for trip_id, count in by_trip}

        return MemoryStatistics(
            total_memories=total,
            memories_this_year=this_year,
            memories_by_trip=memories_by_trip,
        )

    def _get_expense_statistics(self, user_id: UUID) -> ExpenseStatistics:
        """Get expense statistics."""
        total = (
            self.db.query(func.count(Expense.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        by_currency = (
            self.db.query(Expense.currency, func.sum(Expense.amount))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .group_by(Expense.currency)
            .all()
        )
        total_by_currency = {
            currency: float(amount) for currency, amount in by_currency if currency
        }

        by_category = (
            self.db.query(Expense.category, func.sum(Expense.amount))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .group_by(Expense.category)
            .all()
        )
        expenses_by_category = {
            cat: float(amount) for cat, amount in by_category if cat
        }

        # Average expense
        avg = (
            self.db.query(func.avg(Expense.amount))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        return ExpenseStatistics(
            total_expenses=total,
            total_amount_by_currency=total_by_currency,
            expenses_by_category=expenses_by_category,
            average_expense=round(float(avg), 2),
        )

    def _get_packing_statistics(self, user_id: UUID) -> PackingStatistics:
        """Get packing statistics."""
        total = (
            self.db.query(func.count(PackingItem.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        packed = (
            self.db.query(func.count(PackingItem.id))
            .join(Trip)
            .filter(and_(Trip.user_id == user_id, PackingItem.is_packed == True))
            .scalar()
            or 0
        )

        rate = (packed / total * 100) if total > 0 else 0

        return PackingStatistics(
            total_packing_items=total,
            packed_items=packed,
            packing_completion_rate=round(rate, 1),
        )

    def _get_social_statistics(self, user_id: UUID) -> SocialStatistics:
        """Get social statistics."""
        shared = (
            self.db.query(func.count(TripShare.id))
            .filter(TripShare.owner_id == user_id)
            .scalar()
            or 0
        )

        shared_with_me = (
            self.db.query(func.count(TripShare.id))
            .filter(
                and_(
                    TripShare.shared_with_user_id == user_id,
                    TripShare.status == "accepted",
                )
            )
            .scalar()
            or 0
        )

        templates = (
            self.db.query(func.count(TripTemplate.id))
            .filter(TripTemplate.user_id == user_id)
            .scalar()
            or 0
        )

        templates_used = (
            self.db.query(func.sum(TripTemplate.use_count))
            .filter(TripTemplate.user_id == user_id)
            .scalar()
            or 0
        )

        return SocialStatistics(
            trips_shared=shared,
            trips_shared_with_me=shared_with_me,
            templates_created=templates,
            templates_used_by_others=templates_used,
        )

    def _get_total_days_traveled(self, user_id: UUID) -> int:
        """Get total days traveled."""
        trips = (
            self.db.query(Trip)
            .filter(and_(Trip.user_id == user_id, Trip.status == "completed"))
            .all()
        )

        total_days = 0
        for trip in trips:
            if trip.start_date and trip.end_date:
                days = (
                    datetime.strptime(trip.end_date, "%Y-%m-%d")
                    - datetime.strptime(trip.start_date, "%Y-%m-%d")
                ).days + 1
                total_days += days

        return total_days

    def _get_achievement_points(self, user_id: UUID) -> int:
        """Get total achievement points."""
        points = (
            self.db.query(func.sum(Achievement.points))
            .join(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.earned_at.isnot(None),
                )
            )
            .scalar()
            or 0
        )
        return points
