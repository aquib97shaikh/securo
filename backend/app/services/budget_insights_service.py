"""Rule-based budget insights engine.

Analyses budget-vs-actual data, monthly trends, recurring transactions
and goal pacing to surface actionable tips. Every insight is deterministic
— no LLM dependency — so the feature works with zero configuration.
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.budget_insights import BudgetInsight
from app.schemas.budget import BudgetVsActual
from app.services.budget_service import get_budget_vs_actual
from app.services.dashboard_service import get_monthly_trend
from app.services.goal_service import get_goals


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _pct(part: Decimal, whole: Decimal) -> float:
    if whole == 0:
        return 0.0
    return round(float(part / whole * 100), 1)


# ---------------------------------------------------------------------------
# Individual insight generators
# ---------------------------------------------------------------------------

def _over_budget_insights(
    comparisons: list[BudgetVsActual], month: date
) -> list[BudgetInsight]:
    """Categories whose projected spending exceeds the budget by >= 10 %."""
    insights: list[BudgetInsight] = []
    mk = _month_key(month)
    for c in comparisons:
        if c.budget_amount is None or c.budget_amount <= 0:
            continue
        if c.projected_amount <= c.budget_amount:
            continue
        over_pct = _pct(c.projected_amount - c.budget_amount, c.budget_amount)
        if over_pct < 10:
            continue
        insights.append(BudgetInsight(
            id=f"over_budget_{c.category_id}_{mk}",
            type="over_budget",
            severity="warning",
            title=f"{c.category_name} is over budget",
            description=(
                f"{c.category_name} spending is projected at "
                f"{_pct(c.projected_amount, c.budget_amount):.0f}% of your "
                f"budget — {over_pct:.0f}% over."
            ),
            category_id=c.category_id,
            amount=c.projected_amount - c.budget_amount,
            suggestion=f"Consider reviewing your {c.category_name} expenses this month.",
            action_url=f"/budgets",
        ))
    return insights


def _under_budget_insights(
    comparisons: list[BudgetVsActual], month: date
) -> list[BudgetInsight]:
    """Categories using less than 50 % of their budget — a positive signal."""
    insights: list[BudgetInsight] = []
    mk = _month_key(month)
    for c in comparisons:
        if c.budget_amount is None or c.budget_amount <= 0:
            continue
        pct_used = _pct(c.projected_amount, c.budget_amount)
        if pct_used >= 50 or pct_used == 0:
            continue
        insights.append(BudgetInsight(
            id=f"under_budget_{c.category_id}_{mk}",
            type="under_budget",
            severity="success",
            title=f"{c.category_name} is well under budget",
            description=(
                f"Only {pct_used:.0f}% of your {c.category_name} budget used so far."
            ),
            category_id=c.category_id,
            amount=c.budget_amount - c.projected_amount,
            suggestion=f"Great job keeping {c.category_name} spending in check!",
        ))
    return insights


def _no_budget_high_spend_insights(
    comparisons: list[BudgetVsActual], month: date
) -> list[BudgetInsight]:
    """Top-3 spending categories that have no budget set."""
    unbudgeted = [
        c for c in comparisons
        if c.budget_amount is None and c.actual_amount > 0
    ]
    # Sort by actual spending, take top 3.
    unbudgeted.sort(key=lambda c: float(c.actual_amount), reverse=True)
    insights: list[BudgetInsight] = []
    mk = _month_key(month)
    for c in unbudgeted[:3]:
        insights.append(BudgetInsight(
            id=f"no_budget_high_spend_{c.category_id}_{mk}",
            type="no_budget_high_spend",
            severity="info",
            title=f"Consider budgeting for {c.category_name}",
            description=(
                f"You've spent in {c.category_name} this month but have no "
                f"budget set for it."
            ),
            category_id=c.category_id,
            amount=c.actual_amount,
            suggestion=f"Setting a budget for {c.category_name} helps track spending trends.",
            action_url="/budgets",
        ))
    return insights


def _spending_spike_insights(
    comparisons: list[BudgetVsActual], month: date
) -> list[BudgetInsight]:
    """Categories where current month spending is >= 2x previous month."""
    insights: list[BudgetInsight] = []
    mk = _month_key(month)
    for c in comparisons:
        prev = c.prev_month_amount
        if prev <= 0:
            continue
        if c.actual_amount < prev * 2:
            continue
        multiplier = float(c.actual_amount / prev)
        insights.append(BudgetInsight(
            id=f"spending_spike_{c.category_id}_{mk}",
            type="spending_spike",
            severity="warning",
            title=f"{c.category_name} spending spiked",
            description=(
                f"{c.category_name} spending is {multiplier:.1f}× "
                f"higher than last month."
            ),
            category_id=c.category_id,
            amount=c.actual_amount - prev,
            suggestion=f"Check whether the increase in {c.category_name} is expected.",
        ))
    return insights


def _savings_opportunity_insights(
    trends: list[dict], month: date
) -> list[BudgetInsight]:
    """Compare last two months' savings rate."""
    if len(trends) < 2:
        return []

    mk = _month_key(month)
    current = trends[-1]
    previous = trends[-2]

    curr_income = current.get("income", 0)
    curr_expenses = current.get("expenses", 0)
    prev_income = previous.get("income", 0)
    prev_expenses = previous.get("expenses", 0)

    if curr_income <= 0 or prev_income <= 0:
        return []

    curr_savings_rate = (curr_income - curr_expenses) / curr_income * 100
    prev_savings_rate = (prev_income - prev_expenses) / prev_income * 100

    if curr_savings_rate > prev_savings_rate and curr_savings_rate > 0:
        return [BudgetInsight(
            id=f"savings_opportunity_{mk}",
            type="savings_opportunity",
            severity="success",
            title="Your savings rate improved",
            description=(
                f"Savings rate is {curr_savings_rate:.0f}% this month, "
                f"up from {prev_savings_rate:.0f}% last month."
            ),
            amount=Decimal(str(round(curr_income - curr_expenses, 2))),
            suggestion="Keep up the momentum — consider directing the surplus toward a goal.",
            action_url="/goals",
        )]
    elif curr_savings_rate < prev_savings_rate - 5:
        return [BudgetInsight(
            id=f"savings_dip_{mk}",
            type="savings_opportunity",
            severity="info",
            title="Savings rate decreased",
            description=(
                f"Savings rate dropped to {curr_savings_rate:.0f}% from "
                f"{prev_savings_rate:.0f}% last month."
            ),
            amount=Decimal(str(round(curr_income - curr_expenses, 2))),
            suggestion="Review your spending to identify areas where you can save.",
            action_url="/reports",
        )]

    return []


async def _goal_pace_insights(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    month: date,
) -> list[BudgetInsight]:
    """Goals that are behind schedule based on their target date."""
    goals_list = await get_goals(session, workspace_id, user_id, status="active")
    insights: list[BudgetInsight] = []
    mk = _month_key(month)

    for g in goals_list:
        on_track = getattr(g, "on_track", None)
        if on_track in ("behind", "overdue"):
            target_date_str = ""
            if hasattr(g, "target_date") and g.target_date:
                target_date_str = f" by {g.target_date}"
            severity = "warning" if on_track == "behind" else "warning"
            insights.append(BudgetInsight(
                id=f"goal_pace_{g.id}_{mk}",
                type="goal_pace",
                severity=severity,
                title=f"'{g.name}' goal is {on_track.replace('_', ' ')}",
                description=(
                    f"At the current pace, you may not reach your "
                    f"'{g.name}' target{target_date_str}."
                ),
                amount=Decimal(str(g.target_amount - g.current_amount)),
                suggestion="Consider increasing your monthly contribution to get back on track.",
                action_url="/goals",
            ))

    return insights


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def generate_insights(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    month: Optional[date] = None,
) -> list[BudgetInsight]:
    """Generate all budget insights for a given month.

    Returns a deduplicated, severity-sorted list: warnings first, then
    info, then success.
    """
    if not month:
        month = date.today().replace(day=1)
    month = month.replace(day=1)

    # Gather data
    comparisons = await get_budget_vs_actual(session, workspace_id, user_id, month)
    trends_raw = await get_monthly_trend(session, workspace_id, user_id, months=3)
    trends = [{"month": t.month, "income": t.income, "expenses": t.expenses} for t in trends_raw]

    # Generate insights from each rule
    insights: list[BudgetInsight] = []
    insights.extend(_over_budget_insights(comparisons, month))
    insights.extend(_under_budget_insights(comparisons, month))
    insights.extend(_no_budget_high_spend_insights(comparisons, month))
    insights.extend(_spending_spike_insights(comparisons, month))
    insights.extend(_savings_opportunity_insights(trends, month))
    insights.extend(await _goal_pace_insights(session, workspace_id, user_id, month))

    # Deduplicate by id
    seen: set[str] = set()
    unique: list[BudgetInsight] = []
    for i in insights:
        if i.id not in seen:
            seen.add(i.id)
            unique.append(i)

    # Sort: warning > info > success
    severity_order = {"warning": 0, "info": 1, "success": 2}
    unique.sort(key=lambda i: severity_order.get(i.severity, 3))

    return unique
