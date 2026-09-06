"""Data Normalization Layer for Financial Guidance System.

Extracts, converts, and normalizes transactions, budgets, recurring series,
goals, accounts, and payees into a unified deterministic context.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.category_group import CategoryGroup
from app.models.goal import Goal
from app.models.payee import Payee
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.models.user import User
from app.services.account_service import get_accounts
from app.services.budget_service import get_budget_vs_actual
from app.services.fx_rate_service import convert
from app.services.goal_service import get_goals
from app.services.recurring_transaction_service import get_occurrences_in_range


# Known discretionary category indicators
DISCRETIONARY_KEYWORDS = {
    "dining", "restaurant", "food delivery", "takeout", "entertainment",
    "shopping", "clothing", "hobbies", "leisure", "bar", "coffee", "café",
    "electronics", "vacation", "travel", "games", "streaming", "subscriptions"
}


@dataclass
class NormalizedAccount:
    id: uuid.UUID
    name: str
    type: str
    balance_primary: Decimal
    currency: str
    is_credit: bool


@dataclass
class NormalizedTransaction:
    id: uuid.UUID
    date: date
    amount: Decimal  # Positive for expense, negative or type=credit for income
    type: str  # debit, credit
    category_id: Optional[uuid.UUID]
    category_name: str
    account_id: uuid.UUID
    account_name: str
    payee_id: Optional[uuid.UUID]
    payee_name: str
    is_discretionary: bool
    is_recurring: bool


@dataclass
class NormalizedBudget:
    category_id: uuid.UUID
    category_name: str
    budget_amount: Decimal
    actual_amount: Decimal
    projected_amount: Decimal
    variance: Decimal  # actual - budget
    percentage_used: float
    prev_month_amount: Decimal
    is_discretionary: bool


@dataclass
class NormalizedRecurring:
    id: uuid.UUID
    name: str
    amount: Decimal
    type: str  # debit or credit
    frequency: str  # monthly, weekly, yearly, etc.
    category_id: Optional[uuid.UUID]
    category_name: str
    account_id: Optional[uuid.UUID]
    account_name: str
    next_occurrence: Optional[date]
    last_amount: Optional[Decimal]
    price_increase_pct: Optional[float]
    is_overdue: bool
    is_subscription: bool


@dataclass
class NormalizedGoal:
    id: uuid.UUID
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: Optional[date]
    on_track: str  # on_track, behind, overdue, completed
    monthly_target_contribution: Decimal
    shortfall_amount: Decimal


@dataclass
class CashFlowDay:
    date: date
    starting_balance: Decimal
    inflows: Decimal
    outflows: Decimal
    ending_balance: Decimal
    has_shortfall: bool
    events: list[str] = field(default_factory=list)


@dataclass
class NormalizedGuidanceContext:
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    primary_currency: str
    today: date
    target_month: date
    days_in_month: int
    days_elapsed: int

    # Balances
    liquid_balance: Decimal
    total_credit_debt: Decimal
    safety_buffer: Decimal

    # Entities
    accounts: list[NormalizedAccount] = field(default_factory=list)
    current_month_txs: list[NormalizedTransaction] = field(default_factory=list)
    prior_month_txs: list[NormalizedTransaction] = field(default_factory=list)
    history_90d_txs: list[NormalizedTransaction] = field(default_factory=list)
    budgets: list[NormalizedBudget] = field(default_factory=list)
    recurring_items: list[NormalizedRecurring] = field(default_factory=list)
    goals: list[NormalizedGoal] = field(default_factory=list)

    # Cash Flow Forecast (next 30 days)
    cashflow_30d: list[CashFlowDay] = field(default_factory=list)
    projected_shortfall_day: Optional[date] = None
    min_projected_balance: Decimal = Decimal("0.00")

    # Aggregates
    monthly_income: Decimal = Decimal("0.00")
    monthly_expenses: Decimal = Decimal("0.00")
    prior_monthly_income: Decimal = Decimal("0.00")
    prior_monthly_expenses: Decimal = Decimal("0.00")
    avg_90d_monthly_expenses: Decimal = Decimal("0.00")
    savings_rate: float = 0.0
    prior_savings_rate: float = 0.0


def _month_start_end(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def _days_in_month(d: date) -> int:
    s, e = _month_start_end(d.year, d.month)
    return (e - s).days


async def build_guidance_context(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    target_month: Optional[date] = None,
    safety_buffer: Decimal = Decimal("0.00"),
) -> NormalizedGuidanceContext:
    """Load and normalize all workspace primitives into a unified guidance context."""
    today = date.today()
    if not target_month:
        target_month = today.replace(day=1)
    else:
        target_month = target_month.replace(day=1)

    user = await session.get(User, user_id)
    primary_currency = user.primary_currency if user else get_settings().default_currency

    days_in_month = _days_in_month(target_month)
    is_current_month = (target_month.year == today.year and target_month.month == today.month)
    days_elapsed = today.day if is_current_month else days_in_month

    # 1. Accounts & Balances
    raw_accounts = await get_accounts(session, workspace_id, include_closed=False)
    accounts: list[NormalizedAccount] = []
    liquid_balance = Decimal("0.00")
    total_credit_debt = Decimal("0.00")

    account_name_map: dict[uuid.UUID, str] = {}
    for acc in raw_accounts:
        acc_id = uuid.UUID(str(acc.get("id")))
        name = acc.get("display_name") or acc.get("name") or "Account"
        account_name_map[acc_id] = name
        acc_type = acc.get("type", "checking")
        raw_bal = Decimal(str(acc.get("balance", 0)))
        cur = acc.get("currency", primary_currency)
        is_credit = acc_type == "credit_card"

        if cur != primary_currency and raw_bal != 0:
            bal_prim, _ = await convert(session, raw_bal, cur, primary_currency)
        else:
            bal_prim = raw_bal

        accounts.append(
            NormalizedAccount(
                id=acc_id,
                name=name,
                type=acc_type,
                balance_primary=round(bal_prim, 2),
                currency=cur,
                is_credit=is_credit,
            )
        )

        if is_credit:
            if bal_prim < 0:
                total_credit_debt += abs(bal_prim)
        else:
            if acc_type in ("checking", "savings", "cash", "wallet", "current"):
                liquid_balance += bal_prim

    # 2. Categories lookup & classification
    cat_stmt = select(Category).where(Category.workspace_id == workspace_id)
    cat_res = await session.execute(cat_stmt)
    cat_map: dict[uuid.UUID, Category] = {c.id: c for c in cat_res.scalars().all()}

    def check_discretionary(cat: Optional[Category]) -> bool:
        if not cat:
            return True
        name = (cat.name or "").lower()
        for kw in DISCRETIONARY_KEYWORDS:
            if kw in name:
                return True
        return False

    # 3. Time windows for transactions
    cur_start, cur_end = _month_start_end(target_month.year, target_month.month)
    # Prior month
    if target_month.month == 1:
        prior_m = target_month.replace(year=target_month.year - 1, month=12, day=1)
    else:
        prior_m = target_month.replace(month=target_month.month - 1, day=1)
    prior_start, prior_end = _month_start_end(prior_m.year, prior_m.month)

    # 90 days history
    start_90d = today - timedelta(days=90)

    # Fetch transactions from 90 days ago through end of current month
    earliest_date = min(start_90d, prior_start, cur_start)
    latest_date = max(today, cur_end)

    tx_stmt = (
        select(Transaction)
        .where(
            Transaction.workspace_id == workspace_id,
            Transaction.date >= earliest_date,
            Transaction.date <= latest_date,
            Transaction.is_ignored == False,  # noqa: E712
        )
        .order_by(Transaction.date.desc())
    )
    tx_res = await session.execute(tx_stmt)
    all_txs_raw = list(tx_res.scalars().all())

    current_month_txs: list[NormalizedTransaction] = []
    prior_month_txs: list[NormalizedTransaction] = []
    history_90d_txs: list[NormalizedTransaction] = []

    cur_income = Decimal("0.00")
    cur_expenses = Decimal("0.00")
    prior_income = Decimal("0.00")
    prior_expenses = Decimal("0.00")
    exp_90d_total = Decimal("0.00")

    for t in all_txs_raw:
        amt = Decimal(str(t.amount_primary if t.amount_primary is not None else t.amount))
        cat = cat_map.get(t.category_id) if t.category_id else None
        cat_name = cat.name if cat else "Uncategorized"
        is_disc = check_discretionary(cat)
        acc_name = account_name_map.get(t.account_id, "Account")
        payee_name = t.description or "Unknown Merchant"

        norm_tx = NormalizedTransaction(
            id=t.id,
            date=t.date,
            amount=amt,
            type=t.type,
            category_id=t.category_id,
            category_name=cat_name,
            account_id=t.account_id,
            account_name=acc_name,
            payee_id=t.payee_id,
            payee_name=payee_name,
            is_discretionary=is_disc,
            is_recurring=bool(getattr(t, "recurring_transaction_id", None)),
        )

        if cur_start <= t.date < cur_end:
            current_month_txs.append(norm_tx)
            if t.type == "credit":
                cur_income += amt
            elif t.type == "debit":
                cur_expenses += amt

        if prior_start <= t.date < prior_end:
            prior_month_txs.append(norm_tx)
            if t.type == "credit":
                prior_income += amt
            elif t.type == "debit":
                prior_expenses += amt

        if start_90d <= t.date <= today:
            history_90d_txs.append(norm_tx)
            if t.type == "debit":
                exp_90d_total += amt

    avg_90d_monthly_expenses = round(exp_90d_total / Decimal("3.0"), 2)

    cur_savings_rate = 0.0
    if cur_income > 0:
        cur_savings_rate = round(float((cur_income - cur_expenses) / cur_income * 100), 1)

    prior_savings_rate = 0.0
    if prior_income > 0:
        prior_savings_rate = round(float((prior_income - prior_expenses) / prior_income * 100), 1)

    # 4. Budgets
    comparisons = await get_budget_vs_actual(session, workspace_id, user_id, target_month)
    budgets: list[NormalizedBudget] = []
    for c in comparisons:
        if c.budget_amount is not None or c.actual_amount > 0:
            b_amt = c.budget_amount or Decimal("0.00")
            cat = cat_map.get(c.category_id)
            is_disc = check_discretionary(cat)
            pct = c.percentage_used if c.percentage_used is not None else 0.0
            budgets.append(
                NormalizedBudget(
                    category_id=c.category_id,
                    category_name=c.category_name,
                    budget_amount=b_amt,
                    actual_amount=c.actual_amount,
                    projected_amount=c.projected_amount,
                    variance=c.actual_amount - b_amt,
                    percentage_used=pct,
                    prev_month_amount=c.prev_month_amount,
                    is_discretionary=is_disc,
                )
            )

    # 5. Recurring Transactions & Bills
    rec_stmt = select(RecurringTransaction).where(
        RecurringTransaction.workspace_id == workspace_id,
        RecurringTransaction.is_active == True,  # noqa: E712
    )
    rec_res = await session.execute(rec_stmt)
    raw_recurring = list(rec_res.scalars().all())

    recurring_items: list[NormalizedRecurring] = []
    for r in raw_recurring:
        amt = Decimal(str(r.amount_primary if getattr(r, "amount_primary", None) else r.amount))
        cat = cat_map.get(r.category_id) if r.category_id else None
        cat_name = cat.name if cat else "Uncategorized"
        acc_name = account_name_map.get(r.account_id, "Account") if r.account_id else "General"
        rec_name = getattr(r, "description", None) or "Recurring"
        is_sub = any(
            kw in rec_name.lower() for kw in ("sub", "netflix", "spotify", "prime", "icloud", "plan")
        )

        # Look for past transactions linked to this recurring item to detect price increases
        linked_txs = [t for t in history_90d_txs if getattr(t, "is_recurring", False) and t.category_id == r.category_id]
        last_amt: Optional[Decimal] = None
        price_increase_pct: Optional[float] = None
        if len(linked_txs) >= 2:
            older_amt = linked_txs[-1].amount
            if older_amt > 0 and amt > older_amt:
                last_amt = older_amt
                price_increase_pct = round(float((amt - older_amt) / older_amt * 100), 1)

        # Check next occurrence in next 30 days
        next_occ = getattr(r, "next_occurrence", None)
        is_overdue = False
        if next_occ and next_occ < today:
            is_overdue = True

        recurring_items.append(
            NormalizedRecurring(
                id=r.id,
                name=rec_name,
                amount=amt,
                type=r.type,
                frequency=r.frequency,
                category_id=r.category_id,
                category_name=cat_name,
                account_id=r.account_id,
                account_name=acc_name,
                next_occurrence=next_occ,
                last_amount=last_amt,
                price_increase_pct=price_increase_pct,
                is_overdue=is_overdue,
                is_subscription=is_sub,
            )
        )

    # 6. Goals
    raw_goals = await get_goals(session, workspace_id, user_id, status="active")
    goals: list[NormalizedGoal] = []
    for g in raw_goals:
        cur_amt = Decimal(str(g.current_amount))
        tgt_amt = Decimal(str(g.target_amount))
        shortfall = max(Decimal("0.00"), tgt_amt - cur_amt)
        on_track = getattr(g, "on_track", None) or "on_track"

        monthly_needed = Decimal(str(g.monthly_contribution)) if getattr(g, "monthly_contribution", None) else Decimal("0.00")
        if monthly_needed == 0 and g.target_date and g.target_date > today:
            months_left = max(1, (g.target_date.year - today.year) * 12 + (g.target_date.month - today.month))
            monthly_needed = round(shortfall / Decimal(str(months_left)), 2)

        goals.append(
            NormalizedGoal(
                id=g.id,
                name=g.name,
                target_amount=tgt_amt,
                current_amount=cur_amt,
                target_date=g.target_date,
                on_track=on_track,
                monthly_target_contribution=monthly_needed,
                shortfall_amount=shortfall,
            )
        )

    # 7. Cash-Flow Forecast (14-day & 30-day projection)
    # Project daily running balances starting with current liquid balance
    running_bal = liquid_balance
    cashflow_30d: list[CashFlowDay] = []
    min_bal = running_bal
    shortfall_day: Optional[date] = None

    # Calculate average daily discretionary burn from current month
    daily_discretionary_burn = Decimal("0.00")
    if days_elapsed > 0:
        disc_expenses = sum(t.amount for t in current_month_txs if t.type == "debit" and t.is_discretionary)
        daily_discretionary_burn = round(disc_expenses / Decimal(str(days_elapsed)), 2)

    for day_offset in range(30):
        forecast_date = today + timedelta(days=day_offset)
        day_inflows = Decimal("0.00")
        day_outflows = Decimal("0.00")
        day_events: list[str] = []

        # Check recurring transactions hitting on this day
        for rec in recurring_items:
            if rec.next_occurrence == forecast_date:
                if rec.type == "credit":
                    day_inflows += rec.amount
                    day_events.append(f"Income: {rec.name} (+{rec.amount})")
                else:
                    day_outflows += rec.amount
                    day_events.append(f"Bill: {rec.name} (-{rec.amount})")

        # Include estimated daily discretionary spend
        day_outflows += daily_discretionary_burn

        start_day_bal = running_bal
        running_bal = running_bal + day_inflows - day_outflows
        has_shortfall = running_bal < safety_buffer

        if has_shortfall and shortfall_day is None:
            shortfall_day = forecast_date

        if running_bal < min_bal:
            min_bal = running_bal

        cashflow_30d.append(
            CashFlowDay(
                date=forecast_date,
                starting_balance=round(start_day_bal, 2),
                inflows=round(day_inflows, 2),
                outflows=round(day_outflows, 2),
                ending_balance=round(running_bal, 2),
                has_shortfall=has_shortfall,
                events=day_events,
            )
        )

    return NormalizedGuidanceContext(
        workspace_id=workspace_id,
        user_id=user_id,
        primary_currency=primary_currency,
        today=today,
        target_month=target_month,
        days_in_month=days_in_month,
        days_elapsed=days_elapsed,
        liquid_balance=round(liquid_balance, 2),
        total_credit_debt=round(total_credit_debt, 2),
        safety_buffer=safety_buffer,
        accounts=accounts,
        current_month_txs=current_month_txs,
        prior_month_txs=prior_month_txs,
        history_90d_txs=history_90d_txs,
        budgets=budgets,
        recurring_items=recurring_items,
        goals=goals,
        cashflow_30d=cashflow_30d,
        projected_shortfall_day=shortfall_day,
        min_projected_balance=round(min_bal, 2),
        monthly_income=round(cur_income, 2),
        monthly_expenses=round(cur_expenses, 2),
        prior_monthly_income=round(prior_income, 2),
        prior_monthly_expenses=round(prior_expenses, 2),
        avg_90d_monthly_expenses=avg_90d_monthly_expenses,
        savings_rate=cur_savings_rate,
        prior_savings_rate=prior_savings_rate,
    )
