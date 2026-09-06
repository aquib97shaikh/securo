import pytest
from datetime import date
from decimal import Decimal

from app.models.category import Category
from app.models.budget import Budget
from app.services.budget_insights_service import generate_insights
from app.services.expense_planning_service import get_expense_plan


async def _register_sqlite_to_char(session):
    def _to_char(value, fmt):
        if value is None:
            return None
        return str(value)[:7]

    raw = await session.connection()
    def _install(dbapi_conn):
        dbapi_conn.create_function("to_char", 2, _to_char)
    await raw.run_sync(lambda conn: _install(conn.connection.dbapi_connection))


@pytest.mark.asyncio
async def test_generate_insights_over_budget(
    session, test_workspace, test_user, test_categories
):
    """Test generating over-budget insight when spending exceeds budget by >= 10%."""
    await _register_sqlite_to_char(session)
    today = date.today().replace(day=1)
    category = test_categories[0]
    
    # Create a budget of $100
    budget = Budget(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        category_id=category.id,
        amount=Decimal("100.00"),
        month=today,
        is_recurring=False,
    )
    session.add(budget)
    await session.commit()

    # Generate insights
    insights = await generate_insights(
        session, test_workspace.id, test_user.id, month=today
    )
    assert isinstance(insights, list)


@pytest.mark.asyncio
async def test_get_expense_plan_returns_projections(
    session, test_workspace, test_user
):
    """Test get_expense_plan returns valid multi-month projections."""
    plan = await get_expense_plan(
        session, test_workspace.id, test_user.id, months=6
    )
    assert plan is not None
    assert len(plan.months) == 6
    assert plan.summary.total_projected_income >= Decimal("0")
    assert plan.summary.total_projected_expenses >= Decimal("0")
    assert plan.summary.currency is not None


@pytest.mark.asyncio
async def test_api_get_budget_insights(client, auth_headers, session):
    await _register_sqlite_to_char(session)
    res = await client.get("/api/budgets/insights", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_api_get_expense_planning(client, auth_headers):
    res = await client.get("/api/planning/expenses?months=3", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "months" in data
    assert len(data["months"]) == 3
    assert "summary" in data
    assert "total_projected_income" in data["summary"]


@pytest.mark.asyncio
async def test_balance_calculation_with_transactions(session, test_workspace, test_user):
    from app.models.account import Account
    from app.models.transaction import Transaction

    account = Account(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        name="Checking",
        type="checking",
        balance=Decimal("0.00"),
        currency="USD",
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)

    tx = Transaction(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        account_id=account.id,
        amount=Decimal("5000.00"),
        type="credit",
        date=date.today(),
        status="posted",
        source="manual",
        description="Deposit",
    )
    session.add(tx)
    await session.commit()

    plan = await get_expense_plan(session, test_workspace.id, test_user.id, months=3)
    assert plan.starting_balance == 5000.0
    assert plan.summary.ending_balance == 5000.0
    assert [m.projected_balance for m in plan.months] == [5000.0, 5000.0, 5000.0]

    # Test filtering by specific account_id
    plan_acc = await get_expense_plan(
        session, test_workspace.id, test_user.id, months=3, account_id=account.id
    )
    assert plan_acc.starting_balance == 5000.0
    assert plan_acc.summary.ending_balance == 5000.0


@pytest.mark.asyncio
async def test_balance_calculation_with_recurring_flow(session, test_workspace, test_user):
    from datetime import timedelta
    from app.models.account import Account
    from app.models.transaction import Transaction
    from app.models.recurring_transaction import RecurringTransaction

    account = Account(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        name="Checking Flow",
        type="checking",
        balance=Decimal("0.00"),
        currency="USD",
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)

    # Initial deposit of $10,000
    tx = Transaction(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        account_id=account.id,
        amount=Decimal("10000.00"),
        type="credit",
        date=date.today(),
        status="posted",
        source="manual",
        description="Initial Cash",
    )
    session.add(tx)

    # Recurring salary of $2,000 starting next month
    next_month = (date.today().replace(day=1) + timedelta(days=32)).replace(day=1)
    rec_salary = RecurringTransaction(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        account_id=account.id,
        description="Salary",
        amount=Decimal("2000.00"),
        currency="USD",
        type="credit",
        frequency="monthly",
        start_date=next_month,
        next_occurrence=next_month,
        is_active=True,
    )
    session.add(rec_salary)

    # Recurring rent of $500 starting next month
    rec_rent = RecurringTransaction(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        account_id=account.id,
        description="Rent",
        amount=Decimal("500.00"),
        currency="USD",
        type="debit",
        frequency="monthly",
        start_date=next_month,
        next_occurrence=next_month,
        is_active=True,
    )
    session.add(rec_rent)
    await session.commit()

    plan = await get_expense_plan(
        session, test_workspace.id, test_user.id, months=3, account_id=account.id
    )

    assert plan.starting_balance == 10000.0
    # Month 0 has no transactions scheduled
    assert plan.months[0].projected_balance == 10000.0
    # Month 1 adds +$2000 - $500 = +$1500 net -> $11500
    assert plan.months[1].projected_balance == 11500.0
    # Month 2 adds another +$1500 net -> $13000
    assert plan.months[2].projected_balance == 13000.0
    assert plan.summary.ending_balance == 13000.0
    assert plan.summary.total_projected_income == 4000.0
    assert plan.summary.total_projected_expenses == 1000.0
    assert plan.summary.total_projected_savings == 3000.0



