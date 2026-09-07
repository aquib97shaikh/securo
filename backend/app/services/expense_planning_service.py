"""Multi-month expense projection and balance forecast service.

Inspired by Actual Budget's Balance Forecast, this combines starting balances,
scheduled recurring transactions, budget allocations, and goal contributions
to project future cash flows, running balances, and predict shortfalls.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.category import Category
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.expense_planning import (
    CategoryProjection,
    ExpensePlan,
    GoalContribution,
    MonthProjection,
    PlanSummary,
    RecurringProjection,
)
from app.services.account_service import get_accounts
from app.services.budget_service import _build_budget_map
from app.services.dashboard_service import _materialized_recurring_occurrences
from app.services.fx_rate_service import convert
from app.services.goal_service import get_goals
from app.services.recurring_transaction_service import get_occurrences_in_range


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_range(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def _advance_month(d: date, n: int) -> date:
    """Return the first day of the month that is *n* months after *d*."""
    total = d.year * 12 + (d.month - 1) + n
    y, m = divmod(total, 12)
    return date(y, m + 1, 1)


# ---------------------------------------------------------------------------
# Core projection & balance forecast builder
# ---------------------------------------------------------------------------

async def get_expense_plan(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    months: int = 6,
    account_id: Optional[uuid.UUID] = None,
    forecast_mode: str = "all",  # all, recurring_only, budget_only
    safety_buffer: Decimal = Decimal("0.00"),
) -> ExpensePlan:
    """Build a multi-month expense plan and balance forecast."""

    user = await session.get(User, user_id)
    primary_currency = user.primary_currency if user else get_settings().default_currency
    today = date.today()
    start_month = today.replace(day=1)

    # 1. Determine starting balance from accounts
    all_accounts = await get_accounts(session, workspace_id, include_closed=False)
    starting_balance = Decimal("0.00")

    if account_id:
        target_acc = next((a for a in all_accounts if str(a.get("id")) == str(account_id)), None)
        if target_acc:
            raw_bal = Decimal(str(target_acc.get("current_balance") or 0))
            cur = target_acc.get("currency", primary_currency)
            if cur != primary_currency:
                bal_conv, _ = await convert(session, raw_bal, cur, primary_currency)
                starting_balance = bal_conv
            else:
                starting_balance = raw_bal
    else:
        # Sum liquid accounts (checking, savings, cash, wallet)
        for acc in all_accounts:
            if acc.get("is_closed"):
                continue
            acc_type = acc.get("type", "")
            if acc_type in ("checking", "savings", "cash", "wallet") or acc_type != "credit_card":
                raw_bal = Decimal(str(acc.get("current_balance") or 0))
                cur = acc.get("currency", primary_currency)
                if cur != primary_currency:
                    bal_conv, _ = await convert(session, raw_bal, cur, primary_currency)
                    starting_balance += bal_conv
                else:
                    starting_balance += raw_bal

    starting_balance = round(starting_balance, 2)

    # 2. Pre-fetch active recurring transactions
    rec_stmt = select(RecurringTransaction).where(
        RecurringTransaction.workspace_id == workspace_id,
        RecurringTransaction.is_active == True,  # noqa: E712
    )
    if account_id:
        rec_stmt = rec_stmt.where(RecurringTransaction.account_id == account_id)
    rec_result = await session.execute(rec_stmt)
    recurring_list = list(rec_result.scalars().all())

    # Pre-fetch categories for recurring items
    cat_ids = {r.category_id for r in recurring_list if r.category_id}
    cat_map: dict[uuid.UUID, tuple[str, str, str]] = {}
    if cat_ids:
        cat_result = await session.execute(
            select(Category.id, Category.name, Category.icon, Category.color)
            .where(Category.id.in_(cat_ids))
        )
        for row in cat_result.all():
            cat_map[row[0]] = (row[1], row[2], row[3])

    # Check for materialized occurrences to prevent double counting
    materialized_occurrences = await _materialized_recurring_occurrences(
        session,
        workspace_id,
        {rec.id for rec in recurring_list},
        start_month,
        _advance_month(start_month, months + 1),
    )

    # 3. Pre-fetch actual spent in Month 0 so far (to calculate remaining budget for month 0)
    actual_spent_month0: dict[uuid.UUID, Decimal] = {}
    if forecast_mode in ("all", "budget_only"):
        spent_stmt = (
            select(
                Transaction.category_id,
                func.sum(func.coalesce(Transaction.amount_primary, Transaction.amount)),
            )
            .where(
                Transaction.workspace_id == workspace_id,
                Transaction.type == "debit",
                Transaction.date >= start_month,
                Transaction.date < today,
                Transaction.category_id.isnot(None),
                Transaction.status == "posted",
                Transaction.is_ignored == False,
            )
            .group_by(Transaction.category_id)
        )
        if account_id:
            spent_stmt = spent_stmt.where(Transaction.account_id == account_id)
        spent_res = await session.execute(spent_stmt)
        for cat_id_val, amt_val in spent_res.all():
            if cat_id_val:
                actual_spent_month0[cat_id_val] = abs(Decimal(str(amt_val or 0)))

    # 4. Pre-fetch goals for contribution calculation (only in 'all' mode, workspace-wide)
    goals_list = []
    if forecast_mode == "all" and not account_id:
        goals_list = await get_goals(session, workspace_id, user_id, status="active")

    month_projections: list[MonthProjection] = []
    cumulative_savings = Decimal("0.00")
    lowest_balance = starting_balance
    lowest_balance_month: Optional[str] = None

    for i in range(months):
        month_date = _advance_month(start_month, i)
        m_start, m_end = _month_range(month_date.year, month_date.month)
        month_key = f"{month_date.year:04d}-{month_date.month:02d}"

        recurring_items: list[RecurringProjection] = []
        month_income = Decimal("0.00")
        month_expenses = Decimal("0.00")
        category_spending: dict[uuid.UUID, Decimal] = {}

        # Process recurring transactions (unless mode is budget_only)
        if forecast_mode in ("all", "recurring_only"):
            for rec in recurring_list:
                occurrences = get_occurrences_in_range(
                    start=rec.next_occurrence,
                    frequency=rec.frequency,
                    end_date=rec.end_date,
                    range_start=m_start,
                    range_end=m_end,
                    intended_day=rec.day_of_month or rec.start_date.day,
                    weekend_adjustment=rec.weekend_adjustment,
                )
                if not occurrences:
                    continue

                cat_name, cat_icon, cat_color = (None, None, None)
                if rec.category_id and rec.category_id in cat_map:
                    cat_name, cat_icon, cat_color = cat_map[rec.category_id]

                amount = Decimal(str(rec.amount))
                if rec.currency != primary_currency:
                    amount, _ = await convert(session, amount, rec.currency, primary_currency)

                for occ_date in occurrences:
                    # Skip if already materialized as a posted transaction
                    if (rec.id, occ_date) in materialized_occurrences:
                        continue
                    # For Month 0 (current month), occurrences before today are already
                    # in starting_balance, so only include occurrences on or after today
                    if i == 0 and occ_date < today:
                        continue

                    recurring_items.append(RecurringProjection(
                        recurring_id=rec.id,
                        description=rec.description,
                        amount=float(round(Decimal(str(rec.amount)), 2)),
                        amount_primary=float(round(amount, 2)),
                        currency=rec.currency,
                        type=rec.type,
                        date=occ_date.isoformat(),
                        category_id=rec.category_id,
                        category_name=cat_name,
                    ))

                    if rec.type == "credit":
                        month_income += amount
                    else:
                        month_expenses += amount
                        if rec.category_id:
                            category_spending[rec.category_id] = (
                                category_spending.get(rec.category_id, Decimal("0.00")) + amount
                            )

        # Budget-based category allocations
        if forecast_mode in ("all", "budget_only"):
            budget_map = await _build_budget_map(session, workspace_id, m_start)
            for cat_id_str, (budget_amount, _is_recurring) in budget_map.items():
                cat_uuid = uuid.UUID(cat_id_str)
                # In Month 0, allocate only remaining budget for this month
                if i == 0:
                    spent_so_far = actual_spent_month0.get(cat_uuid, Decimal("0.00"))
                    effective_budget = max(Decimal("0.00"), budget_amount - spent_so_far)
                else:
                    effective_budget = budget_amount

                if effective_budget > Decimal("0.00"):
                    # If budget_only, allocate all budget amounts
                    # If all, allocate for categories without recurring items
                    if forecast_mode == "budget_only" or cat_uuid not in category_spending:
                        category_spending[cat_uuid] = category_spending.get(cat_uuid, Decimal("0.00")) + effective_budget
                        month_expenses += effective_budget

        # Build category breakdown
        expense_breakdown: list[CategoryProjection] = []
        for cat_uuid, amount in sorted(
            category_spending.items(), key=lambda x: float(x[1]), reverse=True
        ):
            cat_name_str = "Uncategorized"
            cat_icon_str = "circle-help"
            cat_color_str = "#6B7280"
            if cat_uuid in cat_map:
                cat_name_str, cat_icon_str, cat_color_str = cat_map[cat_uuid]
            else:
                cat_row = await session.execute(
                    select(Category.name, Category.icon, Category.color)
                    .where(Category.id == cat_uuid)
                )
                row = cat_row.one_or_none()
                if row:
                    cat_name_str, cat_icon_str, cat_color_str = row[0], row[1], row[2]
                    cat_map[cat_uuid] = (cat_name_str, cat_icon_str, cat_color_str)

            expense_breakdown.append(CategoryProjection(
                category_id=cat_uuid,
                category_name=cat_name_str,
                category_icon=cat_icon_str,
                category_color=cat_color_str,
                projected_amount=float(round(amount, 2)),
            ))

        # Goal contributions
        goal_contributions: list[GoalContribution] = []
        for g in goals_list:
            monthly = getattr(g, "monthly_contribution", None)
            if monthly and monthly > 0:
                goal_contributions.append(GoalContribution(
                    goal_id=g.id,
                    goal_name=g.name,
                    monthly_contribution=float(round(Decimal(str(monthly)), 2)),
                    currency=g.currency,
                    target_date=g.target_date.isoformat() if g.target_date else None,
                    on_track=getattr(g, "on_track", None),
                ))

        # Running balance calculation
        month_savings = month_income - month_expenses
        cumulative_savings += month_savings
        projected_balance = starting_balance + cumulative_savings

        if projected_balance < lowest_balance or lowest_balance_month is None:
            lowest_balance = projected_balance
            lowest_balance_month = month_key

        month_projections.append(MonthProjection(
            month=month_key,
            projected_income=float(round(month_income, 2)),
            projected_expenses=float(round(month_expenses, 2)),
            projected_savings=float(round(month_savings, 2)),
            projected_balance=float(round(projected_balance, 2)),
            expense_breakdown=expense_breakdown,
            recurring_items=recurring_items,
            goal_contributions=goal_contributions,
            cumulative_savings=float(round(cumulative_savings, 2)),
        ))

    # Summary calculations
    total_income = sum(Decimal(str(m.projected_income)) for m in month_projections)
    total_expenses = sum(Decimal(str(m.projected_expenses)) for m in month_projections)
    total_savings = total_income - total_expenses
    n = Decimal(str(max(len(month_projections), 1)))
    ending_balance = (
        Decimal(str(month_projections[-1].projected_balance))
        if month_projections
        else starting_balance
    )

    has_shortfall = lowest_balance < safety_buffer
    shortfall_amount = max(Decimal("0.00"), safety_buffer - lowest_balance) if has_shortfall else Decimal("0.00")

    summary = PlanSummary(
        starting_balance=float(round(starting_balance, 2)),
        ending_balance=float(round(ending_balance, 2)),
        lowest_balance=float(round(lowest_balance, 2)),
        lowest_balance_month=lowest_balance_month,
        has_shortfall=has_shortfall,
        shortfall_amount=float(round(shortfall_amount, 2)),
        safety_buffer=float(round(safety_buffer, 2)),
        total_projected_income=float(round(total_income, 2)),
        total_projected_expenses=float(round(total_expenses, 2)),
        total_projected_savings=float(round(total_savings, 2)),
        avg_monthly_income=float(round(total_income / n, 2)),
        avg_monthly_expenses=float(round(total_expenses / n, 2)),
        avg_monthly_savings=float(round(total_savings / n, 2)),
        currency=primary_currency,
    )

    return ExpensePlan(
        starting_balance=float(round(starting_balance, 2)),
        forecast_mode=forecast_mode,
        account_id=account_id,
        months=month_projections,
        summary=summary,
    )
