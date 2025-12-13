"""Weather cache model for storing weather data."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Date, DateTime, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class WeatherCache(Base):
    """Cache for weather data to reduce API calls."""

    __tablename__ = "weather_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Location coordinates
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)

    # Location info
    location_name = Column(String(255), nullable=True)
    country_code = Column(String(3), nullable=True)

    # Date for the weather data
    date = Column(Date, nullable=False)

    # Weather data as JSON
    weather_data = Column(JSONB, nullable=False, default={})

    # Cache metadata
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Create indexes for efficient lookups
    __table_args__ = (
        Index('ix_weather_cache_location_date', latitude, longitude, date),
        Index('ix_weather_cache_expires', expires_at),
    )
