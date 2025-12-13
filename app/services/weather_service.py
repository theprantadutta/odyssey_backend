"""Weather service for fetching and caching weather data."""
import os
import httpx
from datetime import datetime, timedelta, date
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.weather_cache import WeatherCache
from app.schemas.weather import (
    WeatherData,
    WeatherCondition,
    TemperatureData,
    WindData,
    WeatherForecastItem,
    WeatherForecastResponse,
    TripWeatherResponse,
)


class WeatherService:
    """Service for weather data operations."""

    # Cache duration in hours
    CACHE_DURATION_HOURS = 3

    # OpenWeatherMap API
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv("OPENWEATHER_API_KEY")

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[WeatherData]:
        """Get current weather for a location."""

        # Check cache first
        cached = self._get_cached_weather(latitude, longitude, date.today())
        if cached:
            return self._parse_cached_weather(cached)

        # Fetch from API
        weather_data = await self._fetch_current_weather(latitude, longitude)
        if weather_data:
            # Cache the result
            self._cache_weather(
                latitude=latitude,
                longitude=longitude,
                weather_date=date.today(),
                data=weather_data,
                location_name=weather_data.get("name", ""),
                country_code=weather_data.get("sys", {}).get("country", ""),
            )
            return self._parse_weather_response(weather_data)

        return None

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
    ) -> Optional[WeatherForecastResponse]:
        """Get weather forecast for a location."""

        if not self.api_key:
            return self._get_mock_forecast(latitude, longitude, days)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/forecast",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self.api_key,
                        "units": "metric",
                        "cnt": days * 8,  # 8 forecasts per day (3-hour intervals)
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_forecast_response(data)

        except Exception as e:
            print(f"Error fetching forecast: {e}")

        return self._get_mock_forecast(latitude, longitude, days)

    async def get_trip_weather(
        self,
        trip_id: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> TripWeatherResponse:
        """Get weather forecast for a trip's duration."""

        days = (end_date - start_date).days + 1
        days = min(days, 16)  # API limit

        forecast = await self.get_forecast(latitude, longitude, days)

        if not forecast:
            # Return mock data if API fails
            return self._get_mock_trip_weather(
                trip_id, latitude, longitude, start_date, end_date
            )

        # Filter forecast to trip dates
        trip_forecast = [
            item for item in forecast.forecast
            if start_date <= item.date <= end_date
        ]

        # Generate packing suggestions based on weather
        suggestions = self._generate_packing_suggestions(trip_forecast)

        return TripWeatherResponse(
            trip_id=trip_id,
            location_name=forecast.location_name,
            country_code=forecast.country_code,
            forecast=trip_forecast,
            packing_suggestions=suggestions,
            fetched_at=datetime.utcnow(),
        )

    def _get_cached_weather(
        self,
        latitude: float,
        longitude: float,
        weather_date: date,
    ) -> Optional[WeatherCache]:
        """Get cached weather data if available and not expired."""

        # Round coordinates to reduce cache misses
        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)

        return (
            self.db.query(WeatherCache)
            .filter(
                and_(
                    WeatherCache.latitude == Decimal(str(lat_rounded)),
                    WeatherCache.longitude == Decimal(str(lon_rounded)),
                    WeatherCache.date == weather_date,
                    WeatherCache.expires_at > datetime.utcnow(),
                )
            )
            .first()
        )

    def _cache_weather(
        self,
        latitude: float,
        longitude: float,
        weather_date: date,
        data: dict,
        location_name: str = "",
        country_code: str = "",
    ) -> None:
        """Cache weather data."""

        lat_rounded = round(latitude, 2)
        lon_rounded = round(longitude, 2)

        # Delete old cache entry if exists
        self.db.query(WeatherCache).filter(
            and_(
                WeatherCache.latitude == Decimal(str(lat_rounded)),
                WeatherCache.longitude == Decimal(str(lon_rounded)),
                WeatherCache.date == weather_date,
            )
        ).delete()

        cache_entry = WeatherCache(
            latitude=Decimal(str(lat_rounded)),
            longitude=Decimal(str(lon_rounded)),
            date=weather_date,
            location_name=location_name,
            country_code=country_code,
            weather_data=data,
            fetched_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self.CACHE_DURATION_HOURS),
        )

        self.db.add(cache_entry)
        self.db.commit()

    async def _fetch_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Optional[dict]:
        """Fetch current weather from OpenWeatherMap API."""

        if not self.api_key:
            return self._get_mock_weather_data(latitude, longitude)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/weather",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self.api_key,
                        "units": "metric",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return response.json()

        except Exception as e:
            print(f"Error fetching weather: {e}")

        return self._get_mock_weather_data(latitude, longitude)

    def _parse_weather_response(self, data: dict) -> WeatherData:
        """Parse OpenWeatherMap response into WeatherData."""

        conditions = [
            WeatherCondition(
                id=w["id"],
                main=w["main"],
                description=w["description"],
                icon=w["icon"],
            )
            for w in data.get("weather", [])
        ]

        main = data.get("main", {})
        temperature = TemperatureData(
            temp=main.get("temp", 20),
            feels_like=main.get("feels_like", 20),
            temp_min=main.get("temp_min"),
            temp_max=main.get("temp_max"),
            humidity=main.get("humidity", 50),
            pressure=main.get("pressure", 1013),
        )

        wind_data = data.get("wind", {})
        wind = WindData(
            speed=wind_data.get("speed", 0),
            deg=wind_data.get("deg"),
            gust=wind_data.get("gust"),
        ) if wind_data else None

        sys_data = data.get("sys", {})

        return WeatherData(
            location_name=data.get("name", "Unknown"),
            country_code=sys_data.get("country", ""),
            latitude=data.get("coord", {}).get("lat", 0),
            longitude=data.get("coord", {}).get("lon", 0),
            conditions=conditions,
            temperature=temperature,
            wind=wind,
            visibility=data.get("visibility"),
            clouds=data.get("clouds", {}).get("all"),
            sunrise=datetime.fromtimestamp(sys_data["sunrise"]) if "sunrise" in sys_data else None,
            sunset=datetime.fromtimestamp(sys_data["sunset"]) if "sunset" in sys_data else None,
            data_timestamp=datetime.fromtimestamp(data.get("dt", datetime.utcnow().timestamp())),
            fetched_at=datetime.utcnow(),
        )

    def _parse_cached_weather(self, cached: WeatherCache) -> WeatherData:
        """Parse cached weather data."""
        return self._parse_weather_response(cached.weather_data)

    def _parse_forecast_response(self, data: dict) -> WeatherForecastResponse:
        """Parse forecast response from OpenWeatherMap."""

        city = data.get("city", {})
        location_name = city.get("name", "Unknown")
        country_code = city.get("country", "")
        coord = city.get("coord", {})

        # Group forecasts by date
        daily_forecasts = {}
        for item in data.get("list", []):
            dt = datetime.fromtimestamp(item["dt"])
            day = dt.date()

            if day not in daily_forecasts:
                daily_forecasts[day] = {
                    "temps": [],
                    "conditions": [],
                    "humidity": [],
                    "wind": [],
                    "rain_prob": [],
                }

            main = item.get("main", {})
            daily_forecasts[day]["temps"].append(main.get("temp", 20))
            daily_forecasts[day]["humidity"].append(main.get("humidity", 50))

            if item.get("weather"):
                daily_forecasts[day]["conditions"].extend(item["weather"])

            if item.get("wind"):
                daily_forecasts[day]["wind"].append(item["wind"].get("speed", 0))

            if item.get("pop"):
                daily_forecasts[day]["rain_prob"].append(item["pop"] * 100)

        # Convert to forecast items
        forecast_items = []
        for day, data in sorted(daily_forecasts.items()):
            temps = data["temps"]
            conditions = data["conditions"]

            # Get most common condition
            main_condition = conditions[0] if conditions else {
                "id": 800,
                "main": "Clear",
                "description": "clear sky",
                "icon": "01d",
            }

            forecast_items.append(
                WeatherForecastItem(
                    date=day,
                    conditions=[
                        WeatherCondition(
                            id=main_condition.get("id", 800),
                            main=main_condition.get("main", "Clear"),
                            description=main_condition.get("description", "clear sky"),
                            icon=main_condition.get("icon", "01d"),
                        )
                    ],
                    temp_min=min(temps) if temps else 15,
                    temp_max=max(temps) if temps else 25,
                    humidity=sum(data["humidity"]) // len(data["humidity"]) if data["humidity"] else 50,
                    wind_speed=sum(data["wind"]) / len(data["wind"]) if data["wind"] else None,
                    rain_probability=max(data["rain_prob"]) if data["rain_prob"] else None,
                    description=main_condition.get("description", "clear sky"),
                )
            )

        return WeatherForecastResponse(
            location_name=location_name,
            country_code=country_code,
            latitude=coord.get("lat", 0),
            longitude=coord.get("lon", 0),
            forecast=forecast_items,
            fetched_at=datetime.utcnow(),
        )

    def _generate_packing_suggestions(
        self,
        forecast: List[WeatherForecastItem],
    ) -> List[str]:
        """Generate packing suggestions based on weather forecast."""

        suggestions = []

        if not forecast:
            return ["Check weather closer to your trip for packing suggestions"]

        # Analyze weather patterns
        max_temp = max(f.temp_max for f in forecast)
        min_temp = min(f.temp_min for f in forecast)
        any_rain = any(
            f.rain_probability and f.rain_probability > 30 for f in forecast
        )
        all_conditions = [c.main for f in forecast for c in f.conditions]

        # Temperature-based suggestions
        if max_temp > 30:
            suggestions.append("Pack light, breathable clothing for hot weather")
            suggestions.append("Bring sunscreen and a hat")
        elif max_temp > 20:
            suggestions.append("Pack layers - t-shirts and light jackets")
        elif max_temp > 10:
            suggestions.append("Bring a warm jacket and sweaters")
        else:
            suggestions.append("Pack heavy winter clothing")
            suggestions.append("Consider thermal underwear")

        if min_temp < 10:
            suggestions.append("Evenings will be cool - bring warm layers")

        # Rain suggestions
        if any_rain:
            suggestions.append("Pack a rain jacket or umbrella")
            suggestions.append("Waterproof shoes recommended")

        # Condition-specific suggestions
        if "Snow" in all_conditions:
            suggestions.append("Snow expected - pack waterproof boots")
            suggestions.append("Bring gloves, scarf, and warm hat")

        if "Clear" in all_conditions and max_temp > 20:
            suggestions.append("Sunny days ahead - don't forget sunglasses")

        if "Clouds" in all_conditions and min_temp < 15:
            suggestions.append("Overcast weather - pack a light jacket")

        return suggestions[:6]  # Limit to 6 suggestions

    def _get_mock_weather_data(self, latitude: float, longitude: float) -> dict:
        """Return mock weather data when API is unavailable."""
        return {
            "coord": {"lon": longitude, "lat": latitude},
            "weather": [
                {
                    "id": 800,
                    "main": "Clear",
                    "description": "clear sky",
                    "icon": "01d",
                }
            ],
            "main": {
                "temp": 22,
                "feels_like": 21,
                "temp_min": 18,
                "temp_max": 26,
                "pressure": 1015,
                "humidity": 55,
            },
            "visibility": 10000,
            "wind": {"speed": 3.5, "deg": 180},
            "clouds": {"all": 5},
            "dt": int(datetime.utcnow().timestamp()),
            "sys": {
                "country": "XX",
                "sunrise": int((datetime.utcnow().replace(hour=6, minute=0)).timestamp()),
                "sunset": int((datetime.utcnow().replace(hour=18, minute=0)).timestamp()),
            },
            "name": "Location",
        }

    def _get_mock_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int,
    ) -> WeatherForecastResponse:
        """Return mock forecast data when API is unavailable."""

        forecast_items = []
        today = date.today()

        for i in range(days):
            forecast_items.append(
                WeatherForecastItem(
                    date=today + timedelta(days=i),
                    conditions=[
                        WeatherCondition(
                            id=800,
                            main="Clear",
                            description="clear sky",
                            icon="01d",
                        )
                    ],
                    temp_min=18 + (i % 3),
                    temp_max=25 + (i % 5),
                    humidity=55,
                    wind_speed=3.5,
                    rain_probability=10 if i % 3 == 0 else 0,
                    description="clear sky",
                )
            )

        return WeatherForecastResponse(
            location_name="Location",
            country_code="XX",
            latitude=latitude,
            longitude=longitude,
            forecast=forecast_items,
            fetched_at=datetime.utcnow(),
        )

    def _get_mock_trip_weather(
        self,
        trip_id: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> TripWeatherResponse:
        """Return mock trip weather when API is unavailable."""

        days = (end_date - start_date).days + 1
        forecast = self._get_mock_forecast(latitude, longitude, days)

        return TripWeatherResponse(
            trip_id=trip_id,
            location_name=forecast.location_name,
            country_code=forecast.country_code,
            forecast=forecast.forecast,
            packing_suggestions=[
                "Pack light, breathable clothing",
                "Bring sunscreen and a hat",
                "Consider packing layers for evenings",
            ],
            fetched_at=datetime.utcnow(),
        )

    async def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns count of deleted entries."""

        result = self.db.query(WeatherCache).filter(
            WeatherCache.expires_at < datetime.utcnow()
        ).delete()

        self.db.commit()
        return result
