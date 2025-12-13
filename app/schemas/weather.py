"""Weather schemas for API requests and responses."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WeatherCondition(BaseModel):
    """Individual weather condition."""

    id: int
    main: str  # e.g., "Clear", "Clouds", "Rain"
    description: str  # e.g., "clear sky", "few clouds"
    icon: str  # Icon code for weather icon


class TemperatureData(BaseModel):
    """Temperature information."""

    current: float = Field(alias="temp")
    feels_like: float
    min_temp: Optional[float] = Field(None, alias="temp_min")
    max_temp: Optional[float] = Field(None, alias="temp_max")
    humidity: int
    pressure: int

    class Config:
        populate_by_name = True


class WindData(BaseModel):
    """Wind information."""

    speed: float  # meters/sec
    deg: Optional[int] = None  # Wind direction in degrees
    gust: Optional[float] = None


class WeatherData(BaseModel):
    """Complete weather data for a location."""

    # Location info
    location_name: str
    country_code: str
    latitude: float
    longitude: float

    # Weather condition
    conditions: List[WeatherCondition]
    temperature: TemperatureData
    wind: Optional[WindData] = None

    # Additional data
    visibility: Optional[int] = None  # meters
    clouds: Optional[int] = None  # Cloud coverage percentage
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None

    # Timestamps
    data_timestamp: datetime
    fetched_at: datetime


class WeatherRequest(BaseModel):
    """Request for weather data."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    date: Optional[date] = None  # If None, returns current weather


class WeatherForecastItem(BaseModel):
    """Individual forecast item."""

    date: date
    conditions: List[WeatherCondition]
    temp_min: float
    temp_max: float
    humidity: int
    wind_speed: Optional[float] = None
    rain_probability: Optional[float] = None  # 0-100 percentage
    description: str


class WeatherForecastResponse(BaseModel):
    """Weather forecast response."""

    location_name: str
    country_code: str
    latitude: float
    longitude: float
    forecast: List[WeatherForecastItem]
    fetched_at: datetime


class TripWeatherRequest(BaseModel):
    """Request weather for a trip's location and dates."""

    trip_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    start_date: date
    end_date: date


class TripWeatherResponse(BaseModel):
    """Weather forecast for a trip."""

    trip_id: str
    location_name: str
    country_code: str
    forecast: List[WeatherForecastItem]
    packing_suggestions: List[str]  # Weather-based packing tips
    fetched_at: datetime
