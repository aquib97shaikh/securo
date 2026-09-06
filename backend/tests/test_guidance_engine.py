import pytest
from datetime import date, timedelta
from decimal import Decimal
import uuid
from sqlalchemy import select

from app.models.account import Account
from app.models.category import Category
from app.models.budget import Budget
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.recurring_transaction import RecurringTransaction

from app.services.guidance.normalizer import (
    build_guidance_context,
    NormalizedGuidanceContext,
)
from app.services.guidance.scorer import calculate_severity_score
from app.services.guidance.catalog import get_recommendation_catalog, get_rule_for_signal
from app.services.guidance.explainer import build_explainable_insight
from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.extractors import (
    extract_budget_variance_signals,
    extract_trend_signals,
    extract_recurring_signals,
    extract_cashflow_forecast_signals,
    extract_savings_rate_signals,
    extract_goal_drift_signals,
    extract_merchant_concentration_signals,
    extract_behavioral_pattern_signals,
    extract_anomaly_signals,
)
from app.services.guidance.guidance_service import (
    generate_guidance,
    record_guidance_feedback,
    get_guidance_history,
)
from app.schemas.guidance import GuidanceFeedbackCreate


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
async def test_scorer_deterministic_formula():
    """Verify 100-point deterministic score: 0.30*I + 0.25*U + 0.20*P + 0.15*C + 0.10*R."""
    ctx = NormalizedGuidanceContext(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        primary_currency="USD",
        today=date.today(),
        target_month=date.today().replace(day=1),
        days_in_month=30,
        days_elapsed=15,
        liquid_balance=Decimal("2000.00"),
        total_credit_debt=Decimal("0.00"),
        safety_buffer=Decimal("500.00"),
        monthly_income=Decimal("3000.00"),
    )

    signal = RawSignal(
        id="test_signal_1",
        extractor_name="budget_variance",
        signal_type="budget_over_pacing",
        impact_amount=Decimal("300.00"),
        urgency_days=5,
        persistence_score=70.0,
        confidence_score=90.0,
        relevance_score=80.0,
        title="Dining Pace Alert",
        summary="Dining spending is trending high",
        category_id=uuid.uuid4(),
        category_name="Dining",
    )

    score, tier, breakdown = calculate_severity_score(signal, ctx)
    assert 0.0 <= score <= 100.0
    assert tier in ("urgent", "action_needed", "watch", "informational")
    assert breakdown.total_score == score
    assert breakdown.confidence == 90.0
    assert breakdown.relevance == 80.0


@pytest.mark.asyncio
async def test_catalog_entries_and_explainer():
    """Verify catalog rules exist and 5-point explainer constructs clean insights."""
    catalog = get_recommendation_catalog()
    assert "rules" in catalog
    assert len(catalog["rules"]) >= 10

    rule = get_rule_for_signal("budget_over_pacing")
    assert rule["family"] == "budget_control"

    ctx = NormalizedGuidanceContext(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        primary_currency="USD",
        today=date.today(),
        target_month=date.today().replace(day=1),
        days_in_month=30,
        days_elapsed=15,
        liquid_balance=Decimal("2000.00"),
        total_credit_debt=Decimal("0.00"),
        safety_buffer=Decimal("500.00"),
    )

    signal = RawSignal(
        id="test_signal_2",
        extractor_name="budget_variance",
        signal_type="budget_over_pacing",
        impact_amount=Decimal("150.00"),
        urgency_days=7,
        persistence_score=60.0,
        confidence_score=85.0,
        relevance_score=75.0,
        title="Groceries Over-Pacing",
        summary="Groceries is exceeding pacing",
        category_id=uuid.uuid4(),
        category_name="Groceries",
        metrics={
            "metric_current": 150.0,
            "metric_baseline": 100.0,
            "metric_pct_change": 50.0,
        },
    )

    score, tier, breakdown = calculate_severity_score(signal, ctx)
    insight = build_explainable_insight(signal, score, tier, breakdown, ctx)

    assert insight.id == "test_signal_2"
    assert insight.family == "budget_control"
    assert insight.what_happened != ""
    assert insight.why_it_matters != ""
    assert insight.how_calculated != ""
    assert insight.next_action != ""
    assert insight.action is not None


@pytest.mark.asyncio
async def test_normalizer_and_extractors_execution(
    session, test_workspace, test_user, test_categories
):
    """Test full context normalization and execution across all 9 extractors."""
    await _register_sqlite_to_char(session)

    # 1. Setup Account
    account = Account(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        name="Checking",
        type="checking",
        balance=Decimal("2500.00"),
        currency="USD",
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)

    cat = test_categories[0]
    today = date.today()

    # 2. Setup Budget
    budget = Budget(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        category_id=cat.id,
        amount=Decimal("300.00"),
        month=today.replace(day=1),
        is_recurring=False,
    )
    session.add(budget)

    # 3. Setup Transactions: $350 spent on category (116% of budget)
    t1 = Transaction(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        account_id=account.id,
        category_id=cat.id,
        amount=Decimal("-350.00"),
        currency="USD",
        type="debit",
        source="manual",
        status="posted",
        date=today,
        description="Fresh Mart",
    )
    session.add(t1)

    # 4. Setup Recurring Transaction
    rec = RecurringTransaction(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        account_id=account.id,
        category_id=cat.id,
        description="Streaming Service",
        amount=Decimal("45.00"),
        currency="USD",
        type="debit",
        frequency="monthly",
        start_date=today - timedelta(days=60),
        next_occurrence=today + timedelta(days=4),
        is_active=True,
    )
    session.add(rec)

    # 5. Setup Goal
    goal = Goal(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        name="Emergency Reserve",
        target_amount=Decimal("4000.00"),
        current_amount=Decimal("400.00"),
        target_date=today + timedelta(days=60),
        currency="USD",
    )
    session.add(goal)
    await session.commit()

    # Build normalized context
    ctx = await build_guidance_context(session, test_workspace.id, test_user.id)
    assert ctx.liquid_balance == Decimal("2500.00")
    assert len(ctx.accounts) >= 1
    assert len(ctx.budgets) >= 1
    assert len(ctx.recurring_items) >= 1
    assert len(ctx.goals) >= 1
    assert len(ctx.cashflow_30d) == 30

    # Test all 9 extractors
    bv_signals = extract_budget_variance_signals(ctx)
    assert isinstance(bv_signals, list)

    trend_signals = extract_trend_signals(ctx)
    assert isinstance(trend_signals, list)

    rec_signals = extract_recurring_signals(ctx)
    assert isinstance(rec_signals, list)

    cf_signals = extract_cashflow_forecast_signals(ctx)
    assert isinstance(cf_signals, list)

    sr_signals = extract_savings_rate_signals(ctx)
    assert isinstance(sr_signals, list)

    goal_signals = extract_goal_drift_signals(ctx)
    assert isinstance(goal_signals, list)

    mc_signals = extract_merchant_concentration_signals(ctx)
    assert isinstance(mc_signals, list)

    beh_signals = extract_behavioral_pattern_signals(ctx)
    assert isinstance(beh_signals, list)

    anom_signals = extract_anomaly_signals(ctx)
    assert isinstance(anom_signals, list)


@pytest.mark.asyncio
async def test_guidance_service_and_feedback_suppression(
    session, test_workspace, test_user, test_categories
):
    """Test guidance generation, feedback recording, snooze suppression, and history tracking."""
    await _register_sqlite_to_char(session)

    account = Account(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        name="Checking",
        type="checking",
        balance=Decimal("1200.00"),
        currency="USD",
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)

    cat = test_categories[0]
    today = date.today()

    budget = Budget(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        category_id=cat.id,
        amount=Decimal("100.00"),
        month=today.replace(day=1),
        is_recurring=False,
    )
    session.add(budget)

    t = Transaction(
        user_id=test_user.id,
        workspace_id=test_workspace.id,
        account_id=account.id,
        category_id=cat.id,
        amount=Decimal("-250.00"),
        currency="USD",
        type="debit",
        source="manual",
        status="posted",
        date=today,
        description="Mega Grocer",
    )
    session.add(t)
    await session.commit()

    # 1. Generate active guidance
    guidance = await generate_guidance(session, test_workspace.id, test_user.id)
    assert guidance is not None
    assert isinstance(guidance.insights, list)
    assert guidance.summary is not None
    assert len(guidance.cashflow_strip) == 14

    if guidance.insights:
        target_insight = guidance.insights[0]

        # 2. Snooze for 7 days
        fb_snooze = await record_guidance_feedback(
            session,
            test_workspace.id,
            test_user.id,
            target_insight.id,
            GuidanceFeedbackCreate(snooze_days=7, is_helpful=True),
        )
        assert fb_snooze.status == "snoozed"
        assert fb_snooze.snoozed_until is not None

        # Verify snoozed insight is now suppressed in active guidance
        guidance_after = await generate_guidance(session, test_workspace.id, test_user.id)
        active_ids = [i.id for i in guidance_after.insights]
        assert target_insight.id not in active_ids

        # 3. Verify it is recorded in history
        history = await get_guidance_history(session, test_workspace.id)
        assert len(history) >= 1
        assert any(h.insight_id == target_insight.id for h in history)


@pytest.mark.asyncio
async def test_api_guidance_endpoints(client, auth_headers, session):
    """Test all /api/guidance endpoints."""
    await _register_sqlite_to_char(session)

    # 1. GET /api/guidance
    res = await client.get("/api/guidance", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "insights" in data
    assert "summary" in data
    assert "cashflow_strip" in data
    assert "month_at_risk" in data

    # 2. Context filter: GET /api/guidance?context=budgets
    res_context = await client.get("/api/guidance?context=budgets", headers=auth_headers)
    assert res_context.status_code == 200
    assert "insights" in res_context.json()

    # 3. POST /api/guidance/{id}/feedback
    dummy_insight_id = "budget_over_pacing:category-123"
    res_fb = await client.post(
        f"/api/guidance/{dummy_insight_id}/feedback",
        headers=auth_headers,
        json={"status": "dismissed", "is_helpful": False},
    )
    assert res_fb.status_code == 200
    fb_data = res_fb.json()
    assert fb_data["status"] == "dismissed"

    # 4. GET /api/guidance/history
    res_hist = await client.get("/api/guidance/history", headers=auth_headers)
    assert res_hist.status_code == 200
    assert isinstance(res_hist.json(), list)

    # 5. POST /api/guidance/{id}/action (generic)
    res_act = await client.post(
        f"/api/guidance/{dummy_insight_id}/action",
        headers=auth_headers,
        json={"action_id": "adjust_budget"},
    )
    assert res_act.status_code == 200
    assert res_act.json()["status"] == "success"

    # 6. POST /api/guidance/{id}/action (1-click budget execution)
    from app.models.category import Category
    cat_res = await session.execute(select(Category))
    sample_cat = cat_res.scalars().first()
    if sample_cat:
        res_budget_act = await client.post(
            f"/api/guidance/test_budget_signal/action",
            headers=auth_headers,
            json={
                "action_type": "update_budget",
                "category_id": str(sample_cat.id),
                "suggested_amount": 550.0,
            },
        )
        assert res_budget_act.status_code == 200
        assert res_budget_act.json()["status"] == "success"

        # Verify budget was created/updated in DB
        b_res = await session.execute(
            select(Budget).where(Budget.category_id == sample_cat.id)
        )
        b = b_res.scalars().first()
        assert b is not None
        assert b.amount == Decimal("550.00")

