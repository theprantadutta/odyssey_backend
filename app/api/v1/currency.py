"""Currency API routes."""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.currency_service import CurrencyService
from app.schemas.currency import (
    ExchangeRateResponse,
    ConversionRequest,
    ConversionResponse,
    BulkConversionRequest,
    BulkConversionResponse,
    CurrencyInfo,
)

router = APIRouter(prefix="/currency", tags=["currency"])


@router.get("/rates", response_model=ExchangeRateResponse)
async def get_exchange_rates(
    base: str = Query("USD", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get exchange rates for a base currency."""

    service = CurrencyService(db)
    return await service.get_exchange_rates(base)


@router.post("/convert", response_model=ConversionResponse)
async def convert_currency(
    request: ConversionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert an amount from one currency to another."""

    service = CurrencyService(db)
    return await service.convert(
        from_currency=request.from_currency,
        to_currency=request.to_currency,
        amount=request.amount,
    )


@router.get("/convert", response_model=ConversionResponse)
async def convert_currency_get(
    from_currency: str = Query(..., alias="from", min_length=3, max_length=3),
    to_currency: str = Query(..., alias="to", min_length=3, max_length=3),
    amount: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert an amount from one currency to another (GET method)."""

    service = CurrencyService(db)
    return await service.convert(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
    )


@router.post("/bulk-convert", response_model=BulkConversionResponse)
async def bulk_convert_currencies(
    request: BulkConversionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Convert multiple amounts to a target currency."""

    service = CurrencyService(db)
    return await service.bulk_convert(
        amounts=request.amounts,
        target_currency=request.target_currency,
    )


@router.get("/supported", response_model=List[CurrencyInfo])
async def get_supported_currencies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of supported currencies."""

    service = CurrencyService(db)
    return service.get_supported_currencies()
