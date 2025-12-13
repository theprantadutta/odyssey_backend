"""Weather API routes."""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.weather_service import WeatherService
from app.schemas.weather import (
    WeatherData,
    WeatherForecastResponse,
    TripWeatherRequest,
    TripWeatherResponse,
)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/current", response_model=WeatherData)
async def get_current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current weather for a location."""

    service = WeatherService(db)
    weather = await service.get_current_weather(latitude, longitude)

    if not weather:
        raise HTTPException(
            status_code=503,
            detail="Weather service temporarily unavailable",
        )

    return weather


@router.get("/forecast", response_model=WeatherForecastResponse)
async def get_weather_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(5, ge=1, le=16),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get weather forecast for a location."""

    service = WeatherService(db)
    forecast = await service.get_forecast(latitude, longitude, days)

    if not forecast:
        raise HTTPException(
            status_code=503,
            detail="Weather service temporarily unavailable",
        )

    return forecast


@router.post("/trip", response_model=TripWeatherResponse)
async def get_trip_weather(
    request: TripWeatherRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get weather forecast for a trip's duration with packing suggestions."""

    if request.end_date < request.start_date:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date",
        )

    service = WeatherService(db)
    return await service.get_trip_weather(
        trip_id=request.trip_id,
        latitude=request.latitude,
        longitude=request.longitude,
        start_date=request.start_date,
        end_date=request.end_date,
    )


@router.get("/trip/{trip_id}", response_model=TripWeatherResponse)
async def get_trip_weather_by_id(
    trip_id: str,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get weather forecast for a trip by ID."""

    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date",
        )

    service = WeatherService(db)
    return await service.get_trip_weather(
        trip_id=trip_id,
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
    )
