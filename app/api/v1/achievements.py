"""Achievement API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.achievement_service import AchievementService
from app.schemas.achievement import (
    AchievementResponse,
    UserAchievementsResponse,
    AchievementUnlockResponse,
    LeaderboardResponse,
    UserAchievementResponse,
)

router = APIRouter(prefix="/achievements", tags=["achievements"])


@router.get("", response_model=List[AchievementResponse])
async def get_all_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all available achievements."""
    service = AchievementService(db)
    achievements = service.get_all_achievements()
    return [service._to_achievement_response(a) for a in achievements]


@router.get("/me", response_model=UserAchievementsResponse)
async def get_my_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's achievements."""
    service = AchievementService(db)
    return service.get_user_achievements(current_user.id)


@router.post("/check", response_model=List[AchievementUnlockResponse])
async def check_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check and update user's achievement progress. Returns newly unlocked achievements."""
    service = AchievementService(db)
    return service.check_and_update_achievements(current_user.id)


@router.get("/unseen", response_model=List[UserAchievementResponse])
async def get_unseen_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get achievements that user hasn't seen yet."""
    service = AchievementService(db)
    unseen = service.get_unseen_achievements(current_user.id)
    return [service._to_user_achievement_response(ua) for ua in unseen]


@router.post("/{achievement_id}/seen")
async def mark_achievement_seen(
    achievement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark an achievement as seen."""
    service = AchievementService(db)
    success = service.mark_achievement_seen(current_user.id, achievement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Achievement not found")
    return {"success": True}


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get achievement leaderboard."""
    service = AchievementService(db)
    return service.get_leaderboard(current_user.id, limit)


@router.post("/seed")
async def seed_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed predefined achievements (admin only in production)."""
    service = AchievementService(db)
    count = service.seed_achievements()
    return {"message": f"Seeded {count} achievements"}
