"""Expense endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseListResponse,
    ExpenseSummaryResponse
)
from app.services.expense_service import ExpenseService

router = APIRouter()


@router.get("/", response_model=ExpenseListResponse)
async def list_expenses(
    trip_id: UUID = Query(..., description="Trip ID to get expenses for"),
    category: str = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all expenses for a specific trip (sorted by date descending)

    - **trip_id**: Required trip ID
    - **category**: Optional category filter (food | transport | accommodation | activities | shopping | other)
    """
    expense_service = ExpenseService(db)
    expenses, total, total_amount = expense_service.get_expenses_by_trip(
        trip_id=trip_id,
        user_id=current_user.id,
        category=category
    )

    return {
        "expenses": expenses,
        "total": total,
        "total_amount": total_amount
    }


@router.get("/summary", response_model=ExpenseSummaryResponse)
async def get_expense_summary(
    trip_id: UUID = Query(..., description="Trip ID to get expense summary for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get expense summary by category for a trip

    Returns:
    - **by_category**: List of expense totals grouped by category
    - **total_amount**: Total of all expenses
    - **currency**: Primary currency used
    """
    expense_service = ExpenseService(db)
    summary = expense_service.get_expense_summary(
        trip_id=trip_id,
        user_id=current_user.id
    )

    return summary


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific expense by ID"""
    expense_service = ExpenseService(db)
    expense = expense_service.get_expense_by_id(expense_id, current_user.id)

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return expense


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new expense

    - **trip_id**: ID of the trip this expense belongs to
    - **title**: Expense title (required)
    - **amount**: Expense amount (required, must be positive)
    - **currency**: ISO 4217 currency code (default: USD)
    - **category**: food | transport | accommodation | activities | shopping | other
    - **date**: Date of the expense
    - **notes**: Additional notes (optional)
    """
    expense_service = ExpenseService(db)
    expense = expense_service.create_expense(current_user.id, expense_data)

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found or unauthorized"
        )

    return expense


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: UUID,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update expense (all fields optional)"""
    expense_service = ExpenseService(db)
    expense = expense_service.update_expense(
        expense_id,
        current_user.id,
        expense_data
    )

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete expense"""
    expense_service = ExpenseService(db)
    deleted = expense_service.delete_expense(expense_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return None
