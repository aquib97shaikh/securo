from typing import Optional
import uuid

from pydantic import BaseModel


class CategoryProjection(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_icon: str
    category_color: str
    projected_amount: float


class RecurringProjection(BaseModel):
    recurring_id: uuid.UUID
    description: str
    amount: float
    amount_primary: Optional[float] = None
    currency: str
    type: str  # debit, credit
    date: str  # YYYY-MM-DD
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = None


class GoalContribution(BaseModel):
    goal_id: uuid.UUID
    goal_name: str
    monthly_contribution: float
    currency: str
    target_date: Optional[str] = None
    on_track: Optional[str] = None  # ahead, on_track, behind, overdue, achieved


class MonthProjection(BaseModel):
    month: str  # "2026-10"
    projected_income: float
    projected_expenses: float
    projected_savings: float  # income - expenses
    projected_balance: float  # starting_balance + cumulative_savings
    expense_breakdown: list[CategoryProjection]
    recurring_items: list[RecurringProjection]
    goal_contributions: list[GoalContribution]
    cumulative_savings: float  # running total from start month


class PlanSummary(BaseModel):
    starting_balance: float
    ending_balance: float
    lowest_balance: float
    lowest_balance_month: Optional[str] = None
    has_shortfall: bool = False
    shortfall_amount: float = 0.0
    safety_buffer: float = 0.0
    total_projected_income: float
    total_projected_expenses: float
    total_projected_savings: float
    avg_monthly_income: float
    avg_monthly_expenses: float
    avg_monthly_savings: float
    currency: str


class ExpensePlan(BaseModel):
    starting_balance: float
    forecast_mode: str = "all"  # all, recurring_only, budget_only
    account_id: Optional[uuid.UUID] = None
    months: list[MonthProjection]
    summary: PlanSummary

