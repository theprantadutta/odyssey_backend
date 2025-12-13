"""Currency service for exchange rates and conversions."""
import os
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.models.exchange_rate import ExchangeRate
from app.schemas.currency import (
    ExchangeRateResponse,
    ConversionResponse,
    BulkConversionResponse,
    CurrencyInfo,
    COMMON_CURRENCIES,
)


class CurrencyService:
    """Service for currency conversion operations."""

    # Cache duration in hours
    CACHE_DURATION_HOURS = 24

    # Exchange rate API (using exchangerate-api.com free tier or similar)
    BASE_URL = "https://api.exchangerate-api.com/v4/latest"

    # Fallback API (Open Exchange Rates)
    FALLBACK_URL = "https://open.er-api.com/v6/latest"

    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY")

    async def get_exchange_rates(
        self,
        base_currency: str = "USD",
    ) -> ExchangeRateResponse:
        """Get exchange rates for a base currency."""

        base_currency = base_currency.upper()

        # Check cache first
        cached = self._get_cached_rates(base_currency)
        if cached:
            return ExchangeRateResponse(
                base=cached.base_currency,
                rates=cached.rates,
                fetched_at=cached.fetched_at,
                expires_at=cached.expires_at,
            )

        # Fetch from API
        rates = await self._fetch_rates(base_currency)

        if rates:
            # Cache the result
            self._cache_rates(base_currency, rates)
            return ExchangeRateResponse(
                base=base_currency,
                rates=rates,
                fetched_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=self.CACHE_DURATION_HOURS),
            )

        # Return fallback rates if API fails
        return self._get_fallback_rates(base_currency)

    async def convert(
        self,
        from_currency: str,
        to_currency: str,
        amount: float,
    ) -> ConversionResponse:
        """Convert amount from one currency to another."""

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return ConversionResponse(
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
                converted_amount=amount,
                rate=1.0,
                fetched_at=datetime.utcnow(),
            )

        # Get exchange rates
        rates_response = await self.get_exchange_rates(from_currency)
        rates = rates_response.rates

        if to_currency not in rates:
            raise ValueError(f"Currency {to_currency} not supported")

        rate = rates[to_currency]
        converted_amount = round(amount * rate, 2)

        return ConversionResponse(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
            converted_amount=converted_amount,
            rate=rate,
            fetched_at=rates_response.fetched_at,
        )

    async def bulk_convert(
        self,
        amounts: List[Dict[str, float]],
        target_currency: str,
    ) -> BulkConversionResponse:
        """Convert multiple amounts to a target currency."""

        target_currency = target_currency.upper()
        conversions = []
        total = 0.0

        for item in amounts:
            for currency, amount in item.items():
                conversion = await self.convert(currency, target_currency, amount)
                conversions.append(conversion)
                total += conversion.converted_amount

        return BulkConversionResponse(
            target_currency=target_currency,
            conversions=conversions,
            total=round(total, 2),
            fetched_at=datetime.utcnow(),
        )

    def get_supported_currencies(self) -> List[CurrencyInfo]:
        """Get list of supported currencies."""
        return COMMON_CURRENCIES

    def _get_cached_rates(self, base_currency: str) -> Optional[ExchangeRate]:
        """Get cached exchange rates if available and not expired."""

        return (
            self.db.query(ExchangeRate)
            .filter(
                ExchangeRate.base_currency == base_currency,
                ExchangeRate.expires_at > datetime.utcnow(),
            )
            .first()
        )

    def _cache_rates(self, base_currency: str, rates: Dict[str, float]) -> None:
        """Cache exchange rates."""

        # Delete old cache entry if exists
        self.db.query(ExchangeRate).filter(
            ExchangeRate.base_currency == base_currency
        ).delete()

        cache_entry = ExchangeRate(
            base_currency=base_currency,
            rates=rates,
            fetched_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self.CACHE_DURATION_HOURS),
        )

        self.db.add(cache_entry)
        self.db.commit()

    async def _fetch_rates(self, base_currency: str) -> Optional[Dict[str, float]]:
        """Fetch exchange rates from API."""

        # Try primary API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/{base_currency}",
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("rates", {})

        except Exception as e:
            print(f"Error fetching from primary API: {e}")

        # Try fallback API
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.FALLBACK_URL}/{base_currency}",
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("rates", {})

        except Exception as e:
            print(f"Error fetching from fallback API: {e}")

        return None

    def _get_fallback_rates(self, base_currency: str) -> ExchangeRateResponse:
        """Return hardcoded fallback rates when APIs are unavailable."""

        # Approximate rates as of 2024 (fallback only)
        usd_rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 149.50,
            "AUD": 1.53,
            "CAD": 1.36,
            "CHF": 0.88,
            "CNY": 7.24,
            "INR": 83.12,
            "BDT": 110.0,
            "SGD": 1.34,
            "THB": 35.80,
            "MYR": 4.72,
            "KRW": 1320.0,
            "MXN": 17.15,
            "BRL": 4.97,
            "ZAR": 18.90,
            "NZD": 1.64,
            "AED": 3.67,
            "SAR": 3.75,
        }

        if base_currency == "USD":
            rates = usd_rates
        else:
            # Convert rates to the requested base currency
            if base_currency not in usd_rates:
                rates = usd_rates  # Fallback to USD if currency not found
            else:
                base_rate = usd_rates[base_currency]
                rates = {
                    currency: round(rate / base_rate, 6)
                    for currency, rate in usd_rates.items()
                }

        return ExchangeRateResponse(
            base=base_currency,
            rates=rates,
            fetched_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),  # Shorter cache for fallback
        )

    async def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries. Returns count of deleted entries."""

        result = self.db.query(ExchangeRate).filter(
            ExchangeRate.expires_at < datetime.utcnow()
        ).delete()

        self.db.commit()
        return result
