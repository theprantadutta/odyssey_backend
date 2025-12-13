"""Currency schemas for API requests and responses."""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CurrencyInfo(BaseModel):
    """Currency information."""

    code: str = Field(..., min_length=3, max_length=3)  # ISO 4217 code
    name: str
    symbol: str
    flag_emoji: Optional[str] = None


class ExchangeRateResponse(BaseModel):
    """Exchange rates response."""

    base: str
    rates: Dict[str, float]
    fetched_at: datetime
    expires_at: datetime


class ConversionRequest(BaseModel):
    """Currency conversion request."""

    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    amount: float = Field(..., gt=0)


class ConversionResponse(BaseModel):
    """Currency conversion response."""

    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    rate: float
    fetched_at: datetime


class BulkConversionRequest(BaseModel):
    """Bulk currency conversion request."""

    amounts: List[Dict[str, float]]  # e.g., [{"USD": 100}, {"EUR": 50}]
    target_currency: str = Field(..., min_length=3, max_length=3)


class BulkConversionResponse(BaseModel):
    """Bulk currency conversion response."""

    target_currency: str
    conversions: List[ConversionResponse]
    total: float
    fetched_at: datetime


class TripBudgetConversion(BaseModel):
    """Trip budget conversion request."""

    trip_id: str
    target_currency: str = Field(..., min_length=3, max_length=3)


class ExpenseConversion(BaseModel):
    """Individual expense with conversion."""

    expense_id: str
    original_amount: float
    original_currency: str
    converted_amount: float
    target_currency: str
    rate: float


class TripBudgetConversionResponse(BaseModel):
    """Trip budget conversion response."""

    trip_id: str
    target_currency: str
    expenses: List[ExpenseConversion]
    total_original: Dict[str, float]  # Totals by original currency
    total_converted: float
    fetched_at: datetime


# Common currencies for quick access
COMMON_CURRENCIES = [
    CurrencyInfo(code="USD", name="US Dollar", symbol="$", flag_emoji="🇺🇸"),
    CurrencyInfo(code="EUR", name="Euro", symbol="€", flag_emoji="🇪🇺"),
    CurrencyInfo(code="GBP", name="British Pound", symbol="£", flag_emoji="🇬🇧"),
    CurrencyInfo(code="JPY", name="Japanese Yen", symbol="¥", flag_emoji="🇯🇵"),
    CurrencyInfo(code="AUD", name="Australian Dollar", symbol="A$", flag_emoji="🇦🇺"),
    CurrencyInfo(code="CAD", name="Canadian Dollar", symbol="C$", flag_emoji="🇨🇦"),
    CurrencyInfo(code="CHF", name="Swiss Franc", symbol="Fr", flag_emoji="🇨🇭"),
    CurrencyInfo(code="CNY", name="Chinese Yuan", symbol="¥", flag_emoji="🇨🇳"),
    CurrencyInfo(code="INR", name="Indian Rupee", symbol="₹", flag_emoji="🇮🇳"),
    CurrencyInfo(code="BDT", name="Bangladeshi Taka", symbol="৳", flag_emoji="🇧🇩"),
    CurrencyInfo(code="SGD", name="Singapore Dollar", symbol="S$", flag_emoji="🇸🇬"),
    CurrencyInfo(code="THB", name="Thai Baht", symbol="฿", flag_emoji="🇹🇭"),
    CurrencyInfo(code="MYR", name="Malaysian Ringgit", symbol="RM", flag_emoji="🇲🇾"),
    CurrencyInfo(code="KRW", name="South Korean Won", symbol="₩", flag_emoji="🇰🇷"),
    CurrencyInfo(code="MXN", name="Mexican Peso", symbol="$", flag_emoji="🇲🇽"),
    CurrencyInfo(code="BRL", name="Brazilian Real", symbol="R$", flag_emoji="🇧🇷"),
    CurrencyInfo(code="ZAR", name="South African Rand", symbol="R", flag_emoji="🇿🇦"),
    CurrencyInfo(code="NZD", name="New Zealand Dollar", symbol="NZ$", flag_emoji="🇳🇿"),
    CurrencyInfo(code="AED", name="UAE Dirham", symbol="د.إ", flag_emoji="🇦🇪"),
    CurrencyInfo(code="SAR", name="Saudi Riyal", symbol="﷼", flag_emoji="🇸🇦"),
]
