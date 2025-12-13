"""Exchange rate cache model for storing currency conversion rates."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class ExchangeRate(Base):
    """Cache for exchange rates to reduce API calls."""

    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Base currency (e.g., "USD")
    base_currency = Column(String(3), nullable=False, unique=True)

    # Exchange rates as JSON (e.g., {"EUR": 0.92, "GBP": 0.79, ...})
    rates = Column(JSONB, nullable=False, default={})

    # Cache metadata
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Create index for efficient lookups
    __table_args__ = (
        Index('ix_exchange_rates_base', base_currency),
        Index('ix_exchange_rates_expires', expires_at),
    )


class SupportedCurrency(Base):
    """Supported currencies with display info."""

    __tablename__ = "supported_currencies"

    code = Column(String(3), primary_key=True)  # ISO 4217 code (e.g., "USD")
    name = Column(String(100), nullable=False)  # Full name (e.g., "US Dollar")
    symbol = Column(String(10), nullable=False)  # Symbol (e.g., "$")
    flag_emoji = Column(String(10), nullable=True)  # Country flag
