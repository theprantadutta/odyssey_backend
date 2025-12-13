"""Expense schemas"""
from pydantic import BaseModel, UUID4, Field
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal


class ExpenseBase(BaseModel):
    """Base expense schema"""
    title: str
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)  # ISO 4217 currency code
    category: str = "other"  # food | transport | accommodation | activities | shopping | other
    date: date
    notes: Optional[str] = None


class ExpenseCreate(ExpenseBase):
    """Expense creation request"""
    trip_id: UUID4


class ExpenseUpdate(BaseModel):
    """Expense update request (all fields optional)"""
    title: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(default=None, max_length=3)
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    """Expense response"""
    id: UUID4
    trip_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    """Expense list response"""
    expenses: List[ExpenseResponse]
    total: int
    total_amount: Decimal = Field(default=Decimal("0.00"))


class ExpenseSummary(BaseModel):
    """Expense summary by category"""
    category: str
    total_amount: Decimal
    count: int
    currency: str


class ExpenseSummaryResponse(BaseModel):
    """Expense summary response"""
    by_category: List[ExpenseSummary]
    total_amount: Decimal
    currency: str
