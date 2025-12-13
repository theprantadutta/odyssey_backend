"""Statistics API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.statistics_service import StatisticsService
from app.schemas.statistics import (
    OverallStatistics,
    YearInReviewStats,
    TravelTimeline,
)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("", response_model=OverallStatistics)
async def get_overall_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive user statistics."""
    service = StatisticsService(db)
    return service.get_overall_statistics(current_user.id)


@router.get("/year-in-review", response_model=YearInReviewStats)
async def get_year_in_review(
    year: Optional[int] = Query(None, description="Year for review (defaults to current year)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get year-in-review statistics."""
    service = StatisticsService(db)
    return service.get_year_in_review(current_user.id, year)


@router.get("/timeline", response_model=TravelTimeline)
async def get_travel_timeline(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user's travel timeline."""
    service = StatisticsService(db)
    return service.get_travel_timeline(current_user.id, limit, offset)
