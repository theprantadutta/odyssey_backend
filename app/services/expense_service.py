"""Expense service for CRUD operations and budget tracking"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.expense import Expense
from app.models.trip import Trip
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class ExpenseService:
    """Service for expense management"""

    def __init__(self, db: Session):
        self.db = db

    def get_expenses_by_trip(
        self,
        trip_id: UUID,
        user_id: UUID,
        category: Optional[str] = None
    ) -> tuple[List[Expense], int, Decimal]:
        """
        Get all expenses for a trip (sorted by date descending)

        Returns:
            Tuple of (expenses list, total count, total amount)
        """
        # First verify the trip belongs to the user
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return [], 0, Decimal("0.00")

        query = self.db.query(Expense).filter(Expense.trip_id == trip_id)

        # Filter by category if provided
        if category:
            query = query.filter(Expense.category == category)

        total = query.count()
        total_amount = query.with_entities(
            func.coalesce(func.sum(Expense.amount), 0)
        ).scalar() or Decimal("0.00")

        expenses = query.order_by(Expense.date.desc()).all()

        return expenses, total, total_amount

    def get_expense_by_id(
        self,
        expense_id: UUID,
        user_id: UUID
    ) -> Optional[Expense]:
        """Get a specific expense by ID (with user ownership check via trip)"""
        expense = self.db.query(Expense).filter(Expense.id == expense_id).first()

        if not expense:
            return None

        # Verify ownership through trip
        trip = self.db.query(Trip).filter(
            Trip.id == expense.trip_id,
            Trip.user_id == user_id
        ).first()

        return expense if trip else None

    def create_expense(
        self,
        user_id: UUID,
        expense_data: ExpenseCreate
    ) -> Optional[Expense]:
        """Create a new expense"""
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == expense_data.trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return None

        db_expense = Expense(
            trip_id=expense_data.trip_id,
            title=expense_data.title,
            amount=expense_data.amount,
            currency=expense_data.currency,
            category=expense_data.category,
            date=expense_data.date,
            notes=expense_data.notes,
        )

        self.db.add(db_expense)
        self.db.commit()
        self.db.refresh(db_expense)

        return db_expense

    def update_expense(
        self,
        expense_id: UUID,
        user_id: UUID,
        expense_data: ExpenseUpdate
    ) -> Optional[Expense]:
        """Update an existing expense"""
        expense = self.get_expense_by_id(expense_id, user_id)
        if not expense:
            return None

        # Update only provided fields
        update_data = expense_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)

        expense.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(expense)

        return expense

    def delete_expense(self, expense_id: UUID, user_id: UUID) -> bool:
        """
        Delete an expense

        Returns:
            True if deleted, False if not found
        """
        expense = self.get_expense_by_id(expense_id, user_id)
        if not expense:
            return False

        self.db.delete(expense)
        self.db.commit()

        return True

    def get_expense_summary(
        self,
        trip_id: UUID,
        user_id: UUID
    ) -> dict:
        """
        Get expense summary by category for a trip

        Returns:
            Dict with summary by category and total
        """
        # Verify trip ownership
        trip = self.db.query(Trip).filter(
            Trip.id == trip_id,
            Trip.user_id == user_id
        ).first()

        if not trip:
            return {"by_category": [], "total_amount": Decimal("0.00"), "currency": "USD"}

        # Get summary by category
        category_summary = self.db.query(
            Expense.category,
            func.sum(Expense.amount).label("total_amount"),
            func.count(Expense.id).label("count"),
            Expense.currency
        ).filter(
            Expense.trip_id == trip_id
        ).group_by(
            Expense.category,
            Expense.currency
        ).all()

        by_category = [
            {
                "category": row.category,
                "total_amount": row.total_amount or Decimal("0.00"),
                "count": row.count,
                "currency": row.currency
            }
            for row in category_summary
        ]

        # Calculate total
        total = self.db.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.trip_id == trip_id
        ).scalar() or Decimal("0.00")

        # Get primary currency (most used)
        primary_currency = "USD"
        if by_category:
            primary_currency = max(by_category, key=lambda x: x["count"])["currency"]

        return {
            "by_category": by_category,
            "total_amount": total,
            "currency": primary_currency
        }
