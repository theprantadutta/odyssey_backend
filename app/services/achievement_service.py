"""Achievement service for gamification."""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.achievement import Achievement, UserAchievement
from app.models.user import User
from app.models.trip import Trip
from app.models.activity import Activity
from app.models.memory import Memory
from app.models.expense import Expense
from app.models.packing_item import PackingItem
from app.models.trip_share import TripShare
from app.models.trip_template import TripTemplate
from app.schemas.achievement import (
    AchievementResponse,
    UserAchievementResponse,
    UserAchievementsResponse,
    AchievementUnlockResponse,
    LeaderboardEntry,
    LeaderboardResponse,
    ACHIEVEMENT_DEFINITIONS,
)


class AchievementService:
    """Service for achievement operations."""

    def __init__(self, db: Session):
        self.db = db

    def seed_achievements(self) -> int:
        """Seed predefined achievements into the database."""
        created = 0
        for i, definition in enumerate(ACHIEVEMENT_DEFINITIONS):
            existing = (
                self.db.query(Achievement)
                .filter(Achievement.type == definition["type"])
                .first()
            )
            if not existing:
                achievement = Achievement(
                    type=definition["type"],
                    name=definition["name"],
                    description=definition["description"],
                    icon=definition["icon"],
                    category=definition["category"],
                    threshold=definition["threshold"],
                    tier=definition["tier"],
                    points=definition["points"],
                    sort_order=i,
                )
                self.db.add(achievement)
                created += 1

        self.db.commit()
        return created

    def get_all_achievements(self) -> List[Achievement]:
        """Get all active achievements."""
        return (
            self.db.query(Achievement)
            .filter(Achievement.is_active == True)
            .order_by(Achievement.sort_order)
            .all()
        )

    def get_user_achievements(self, user_id: UUID) -> UserAchievementsResponse:
        """Get user's achievement status."""
        all_achievements = self.get_all_achievements()

        # Get user's achievement records
        user_achievements = (
            self.db.query(UserAchievement)
            .filter(UserAchievement.user_id == user_id)
            .all()
        )

        user_achievement_map = {ua.achievement_id: ua for ua in user_achievements}

        earned = []
        in_progress = []
        locked = []
        total_points = 0

        for achievement in all_achievements:
            user_ach = user_achievement_map.get(achievement.id)

            if user_ach and user_ach.is_earned:
                earned.append(user_ach)
                total_points += achievement.points
            elif user_ach and user_ach.progress > 0:
                in_progress.append(user_ach)
            else:
                locked.append(achievement)

        return UserAchievementsResponse(
            earned=[self._to_user_achievement_response(ua) for ua in earned],
            in_progress=[self._to_user_achievement_response(ua) for ua in in_progress],
            locked=[self._to_achievement_response(a) for a in locked],
            total_points=total_points,
            earned_count=len(earned),
            total_count=len(all_achievements),
        )

    def check_and_update_achievements(
        self, user_id: UUID
    ) -> List[AchievementUnlockResponse]:
        """Check all achievements for a user and update progress."""
        unlocked = []

        # Get user stats
        stats = self._get_user_stats(user_id)

        # Check each achievement type
        achievement_checks = [
            ("first_trip", stats["total_trips"], 1),
            ("trips_5", stats["total_trips"], 5),
            ("trips_10", stats["total_trips"], 10),
            ("trips_25", stats["total_trips"], 25),
            ("first_completed", stats["completed_trips"], 1),
            ("completed_5", stats["completed_trips"], 5),
            ("completed_10", stats["completed_trips"], 10),
            ("first_activity", stats["total_activities"], 1),
            ("activities_25", stats["total_activities"], 25),
            ("activities_100", stats["total_activities"], 100),
            ("first_memory", stats["total_memories"], 1),
            ("memories_50", stats["total_memories"], 50),
            ("memories_200", stats["total_memories"], 200),
            ("first_expense", stats["total_expenses"], 1),
            ("expenses_50", stats["total_expenses"], 50),
            ("first_share", stats["total_shares"], 1),
            ("shares_5", stats["total_shares"], 5),
            ("first_template", stats["total_templates"], 1),
        ]

        for achievement_type, current_value, threshold in achievement_checks:
            result = self._check_achievement(
                user_id, achievement_type, current_value, threshold
            )
            if result:
                unlocked.append(result)

        # Check packing completion separately
        if stats["completed_packing_lists"] >= 1:
            result = self._check_achievement(
                user_id, "packing_complete", stats["completed_packing_lists"], 1
            )
            if result:
                unlocked.append(result)

        if stats["completed_packing_lists"] >= 10:
            result = self._check_achievement(
                user_id, "packing_10", stats["completed_packing_lists"], 10
            )
            if result:
                unlocked.append(result)

        return unlocked

    def _check_achievement(
        self,
        user_id: UUID,
        achievement_type: str,
        current_value: int,
        threshold: int,
    ) -> Optional[AchievementUnlockResponse]:
        """Check and potentially unlock an achievement."""
        achievement = (
            self.db.query(Achievement)
            .filter(Achievement.type == achievement_type)
            .first()
        )

        if not achievement:
            return None

        # Get or create user achievement
        user_achievement = (
            self.db.query(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement.id,
                )
            )
            .first()
        )

        if not user_achievement:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress=0,
            )
            self.db.add(user_achievement)

        # Already earned
        if user_achievement.is_earned:
            return None

        # Update progress
        user_achievement.progress = min(current_value, threshold)

        # Check if now earned
        if current_value >= threshold:
            user_achievement.earned_at = datetime.utcnow()
            self.db.commit()

            return AchievementUnlockResponse(
                achievement=self._to_achievement_response(achievement),
                earned_at=user_achievement.earned_at,
                is_new=True,
            )

        self.db.commit()
        return None

    def mark_achievement_seen(self, user_id: UUID, achievement_id: UUID) -> bool:
        """Mark an achievement as seen by the user."""
        user_achievement = (
            self.db.query(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement_id,
                )
            )
            .first()
        )

        if user_achievement:
            user_achievement.seen = True
            self.db.commit()
            return True

        return False

    def get_unseen_achievements(self, user_id: UUID) -> List[UserAchievement]:
        """Get achievements that user hasn't seen yet."""
        return (
            self.db.query(UserAchievement)
            .filter(
                and_(
                    UserAchievement.user_id == user_id,
                    UserAchievement.earned_at.isnot(None),
                    UserAchievement.seen == False,
                )
            )
            .all()
        )

    def get_leaderboard(
        self, user_id: Optional[UUID] = None, limit: int = 10
    ) -> LeaderboardResponse:
        """Get achievement leaderboard."""
        # Get top users by points
        subquery = (
            self.db.query(
                UserAchievement.user_id,
                func.sum(Achievement.points).label("total_points"),
                func.count(UserAchievement.id).label("earned_count"),
            )
            .join(Achievement)
            .filter(UserAchievement.earned_at.isnot(None))
            .group_by(UserAchievement.user_id)
            .subquery()
        )

        results = (
            self.db.query(
                User.id,
                User.email,
                subquery.c.total_points,
                subquery.c.earned_count,
            )
            .join(subquery, User.id == subquery.c.user_id)
            .order_by(subquery.c.total_points.desc())
            .limit(limit)
            .all()
        )

        entries = []
        for i, (uid, email, points, count) in enumerate(results):
            entries.append(
                LeaderboardEntry(
                    user_id=uid,
                    email=self._mask_email(email),
                    total_points=points or 0,
                    earned_count=count or 0,
                    rank=i + 1,
                )
            )

        # Get current user's rank
        user_rank = None
        user_points = None
        if user_id:
            user_stats = self.get_user_achievements(user_id)
            user_points = user_stats.total_points

            # Find rank
            rank_result = (
                self.db.query(func.count(subquery.c.user_id) + 1)
                .filter(subquery.c.total_points > user_points)
                .scalar()
            )
            user_rank = rank_result or 1

        return LeaderboardResponse(
            entries=entries,
            user_rank=user_rank,
            user_points=user_points,
        )

    def _get_user_stats(self, user_id: UUID) -> dict:
        """Get user's statistics for achievement checking."""
        # Total trips
        total_trips = (
            self.db.query(func.count(Trip.id))
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        # Completed trips
        completed_trips = (
            self.db.query(func.count(Trip.id))
            .filter(and_(Trip.user_id == user_id, Trip.status == "completed"))
            .scalar()
            or 0
        )

        # Total activities (across all user's trips)
        total_activities = (
            self.db.query(func.count(Activity.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        # Total memories
        total_memories = (
            self.db.query(func.count(Memory.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        # Total expenses
        total_expenses = (
            self.db.query(func.count(Expense.id))
            .join(Trip)
            .filter(Trip.user_id == user_id)
            .scalar()
            or 0
        )

        # Total shares (trips shared by user)
        total_shares = (
            self.db.query(func.count(TripShare.id))
            .filter(TripShare.owner_id == user_id)
            .scalar()
            or 0
        )

        # Total templates created
        total_templates = (
            self.db.query(func.count(TripTemplate.id))
            .filter(TripTemplate.user_id == user_id)
            .scalar()
            or 0
        )

        # Completed packing lists (trips where all items are packed)
        # This is a bit complex - count trips where all packing items are packed
        trips_with_packing = (
            self.db.query(Trip.id)
            .filter(Trip.user_id == user_id)
            .join(PackingItem)
            .all()
        )

        completed_packing_lists = 0
        for (trip_id,) in trips_with_packing:
            total_items = (
                self.db.query(func.count(PackingItem.id))
                .filter(PackingItem.trip_id == trip_id)
                .scalar()
                or 0
            )
            packed_items = (
                self.db.query(func.count(PackingItem.id))
                .filter(
                    and_(
                        PackingItem.trip_id == trip_id,
                        PackingItem.is_packed == True,
                    )
                )
                .scalar()
                or 0
            )
            if total_items > 0 and total_items == packed_items:
                completed_packing_lists += 1

        return {
            "total_trips": total_trips,
            "completed_trips": completed_trips,
            "total_activities": total_activities,
            "total_memories": total_memories,
            "total_expenses": total_expenses,
            "total_shares": total_shares,
            "total_templates": total_templates,
            "completed_packing_lists": completed_packing_lists,
        }

    def _to_achievement_response(self, achievement: Achievement) -> AchievementResponse:
        """Convert Achievement model to response schema."""
        return AchievementResponse(
            id=achievement.id,
            type=achievement.type,
            name=achievement.name,
            description=achievement.description,
            icon=achievement.icon,
            category=achievement.category,
            threshold=achievement.threshold,
            tier=achievement.tier,
            points=achievement.points,
            sort_order=achievement.sort_order,
            is_active=achievement.is_active,
            created_at=achievement.created_at,
        )

    def _to_user_achievement_response(
        self, user_achievement: UserAchievement
    ) -> UserAchievementResponse:
        """Convert UserAchievement model to response schema."""
        return UserAchievementResponse(
            id=user_achievement.id,
            user_id=user_achievement.user_id,
            achievement_id=user_achievement.achievement_id,
            progress=user_achievement.progress,
            earned_at=user_achievement.earned_at,
            seen=user_achievement.seen,
            created_at=user_achievement.created_at,
            achievement=self._to_achievement_response(user_achievement.achievement),
        )

    def _mask_email(self, email: str) -> str:
        """Mask email for privacy in leaderboard."""
        parts = email.split("@")
        if len(parts) != 2:
            return "***"
        username = parts[0]
        domain = parts[1]
        if len(username) <= 2:
            masked = username[0] + "*"
        else:
            masked = username[0] + "*" * (len(username) - 2) + username[-1]
        return f"{masked}@{domain}"
