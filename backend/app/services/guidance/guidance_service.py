from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guidance import GuidanceFeedback
from app.schemas.guidance import (
    CashFlowForecastStripItem,
    GuidanceFeedbackCreate,
    GuidanceHistoryItem,
    GuidanceInsight,
    GuidanceResponse,
    GuidanceSummaryStats,
    MonthAtRiskItem,
    SpendingChangeItem,
)
from app.services.guidance.explainer import build_explainable_insight
from app.services.guidance.extractors import (
    extract_anomaly_signals,
    extract_behavioral_pattern_signals,
    extract_budget_variance_signals,
    extract_cashflow_forecast_signals,
    extract_goal_drift_signals,
    extract_merchant_concentration_signals,
    extract_recurring_signals,
    extract_savings_rate_signals,
    extract_trend_signals,
)
from app.services.guidance.normalizer import build_guidance_context
from app.services.guidance.scorer import calculate_severity_score


def _matches_context(ins: GuidanceInsight, context: str) -> bool:
    c = context.strip().lower()
    if c in ("budgets", "budget"):
        return (
            ins.family in ("budget_control",)
            or ins.signal_type.startswith("budget_")
            or ins.evidence.budget is not None
        )
    if c in ("recurring", "bills"):
        return (
            ins.family in ("recurring_optimization",)
            or ins.signal_type.startswith("recurring_")
            or ins.evidence.recurring is not None
        )
    if c in ("goals", "goal"):
        return (
            ins.family in ("savings_growth",)
            or ins.signal_type.startswith("goal_")
            or ins.evidence.goal is not None
        )
    if c in ("transactions", "transaction"):
        return (
            ins.signal_type.startswith("merchant_")
            or ins.signal_type.startswith("anomaly_")
            or ins.signal_type.startswith("weekend_")
            or ins.signal_type.startswith("discretionary_")
            or ins.family in ("budget_control",)
        )
    if c in ("planning", "reports", "forecast"):
        return (
            ins.family in ("cashflow_safety", "savings_growth", "debt_prevention")
            or ins.signal_type.startswith("cashflow_")
        )
    return True


async def generate_guidance(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    target_month: Optional[date] = None,
    safety_buffer: Decimal = Decimal("0.00"),
    context: Optional[str] = None,
    min_score: float = 0.0,
    limit: Optional[int] = None,
) -> GuidanceResponse:
    """Generate complete evidence-backed guidance insights, rankings, forecast strip,

    and month-at-risk analysis for the workspace.
    """
    # 1. Normalize data
    ctx = await build_guidance_context(
        session=session,
        workspace_id=workspace_id,
        user_id=user_id,
        target_month=target_month,
        safety_buffer=safety_buffer,
    )

    # 2. Run all 9 extractors in specified order
    raw_signals = []
    raw_signals.extend(extract_budget_variance_signals(ctx))
    raw_signals.extend(extract_trend_signals(ctx))
    raw_signals.extend(extract_recurring_signals(ctx))
    raw_signals.extend(extract_cashflow_forecast_signals(ctx))
    raw_signals.extend(extract_savings_rate_signals(ctx))
    raw_signals.extend(extract_goal_drift_signals(ctx))
    raw_signals.extend(extract_merchant_concentration_signals(ctx))
    raw_signals.extend(extract_behavioral_pattern_signals(ctx))
    raw_signals.extend(extract_anomaly_signals(ctx))

    # 3. Score and explain each signal
    all_insights: list[GuidanceInsight] = []
    for signal in raw_signals:
        score, severity, breakdown = calculate_severity_score(signal, ctx)
        insight = build_explainable_insight(signal, score, severity, breakdown, ctx)
        all_insights.append(insight)

    # 4. Fetch user feedback & suppression rules from database
    fb_stmt = select(GuidanceFeedback).where(
        GuidanceFeedback.workspace_id == workspace_id
    )
    fb_res = await session.execute(fb_stmt)
    feedbacks = list(fb_res.scalars().all())

    now_utc = datetime.now(timezone.utc)
    dismissed_ids = {f.insight_id for f in feedbacks if f.status == "dismissed"}
    snoozed_ids = {
        f.insight_id
        for f in feedbacks
        if f.status == "snoozed"
        and f.snoozed_until
        and (
            f.snoozed_until.replace(tzinfo=timezone.utc)
            if f.snoozed_until.tzinfo is None
            else f.snoozed_until
        )
        > now_utc
    }

    # 5. Filter suppressed insights and deduplicate
    seen_ids = set()
    active_insights: list[GuidanceInsight] = []
    for ins in all_insights:
        if ins.id in seen_ids or ins.id in dismissed_ids or ins.id in snoozed_ids:
            continue
        seen_ids.add(ins.id)
        active_insights.append(ins)

    # Sort deterministically by 100-point score descending
    active_insights.sort(key=lambda x: x.score, reverse=True)

    # Apply context filter and minimum conviction threshold if specified
    if context:
        active_insights = [
            i for i in active_insights
            if _matches_context(i, context) and i.score >= min_score
        ]
        if limit is not None and limit > 0:
            active_insights = active_insights[:limit]
    elif min_score > 0.0:
        active_insights = [i for i in active_insights if i.score >= min_score]
        if limit is not None and limit > 0:
            active_insights = active_insights[:limit]

    # 6. Calculate summary counts & at-risk amount
    urgent_cnt = sum(1 for i in active_insights if i.severity == "urgent")
    action_cnt = sum(1 for i in active_insights if i.severity == "action_needed")
    watch_cnt = sum(1 for i in active_insights if i.severity == "watch")
    info_cnt = sum(1 for i in active_insights if i.severity == "informational")

    at_risk_amount = sum(
        (i.impact_amount for i in active_insights if i.severity in ("urgent", "action_needed") and i.impact_amount),
        start=Decimal("0.00")
    )

    summary_stats = GuidanceSummaryStats(
        total_active=len(active_insights),
        urgent_count=urgent_cnt,
        action_needed_count=action_cnt,
        watch_count=watch_cnt,
        informational_count=info_cnt,
        total_at_risk_amount=round(at_risk_amount, 2),
    )

    # 7. Cash Flow Forecast Strip (next 14 days)
    cashflow_strip: list[CashFlowForecastStripItem] = []
    for day in ctx.cashflow_30d[:14]:
        day_label = day.date.strftime("%a, %b %d")
        cashflow_strip.append(
            CashFlowForecastStripItem(
                date=str(day.date),
                day_label=day_label,
                projected_balance=day.ending_balance,
                net_change=day.inflows - day.outflows,
                inflows=day.inflows,
                outflows=day.outflows,
                has_shortfall=day.has_shortfall,
                events=day.events,
            )
        )

    # 8. This Month At Risk List
    month_at_risk: list[MonthAtRiskItem] = []
    # Overspent categories
    for b in ctx.budgets:
        if b.actual_amount > b.budget_amount and b.budget_amount > 0:
            month_at_risk.append(
                MonthAtRiskItem(
                    id=f"risk_budget_{b.category_id}",
                    type="category_overspend",
                    name=b.category_name,
                    amount=b.actual_amount - b.budget_amount,
                    severity="urgent" if (b.actual_amount - b.budget_amount) > 100 else "action_needed",
                    status_label=f"Over budget by {b.actual_amount - b.budget_amount}",
                    url="/budgets",
                )
            )

    # Overdue / near-due bills
    for r in ctx.recurring_items:
        if r.type == "debit":
            if r.is_overdue:
                month_at_risk.append(
                    MonthAtRiskItem(
                        id=f"risk_rec_{r.id}",
                        type="missed_payment",
                        name=r.name,
                        amount=r.amount,
                        severity="urgent",
                        status_label="Payment past due",
                        url="/recurring",
                    )
                )
            elif r.next_occurrence and (r.next_occurrence - ctx.today).days <= 3:
                month_at_risk.append(
                    MonthAtRiskItem(
                        id=f"risk_rec_due_{r.id}",
                        type="upcoming_bill",
                        name=r.name,
                        amount=r.amount,
                        severity="action_needed",
                        status_label=f"Due on {r.next_occurrence}",
                        url="/recurring",
                    )
                )

    # Behind goals
    for g in ctx.goals:
        if g.on_track in ("behind", "off_track") and g.target_amount > g.current_amount:
            month_at_risk.append(
                MonthAtRiskItem(
                    id=f"risk_goal_{g.id}",
                    type="goal_behind",
                    name=g.name,
                    amount=g.monthly_target_contribution,
                    severity="watch",
                    status_label="Behind schedule",
                    url="/goals",
                )
            )

    # 9. Spending Changes (Top increases/decreases vs 90d baseline)
    spending_changes: list[SpendingChangeItem] = []
    for b in ctx.budgets:
        if b.actual_amount > Decimal("0.00"):
            base = b.prev_month_amount if b.prev_month_amount > 0 else Decimal("0.00")
            if base > Decimal("0.00"):
                diff = b.actual_amount - base
                chg_pct = round(float(diff / base * 100), 1)
                direction = "increase" if diff > 0 else "decrease"
                spending_changes.append(
                    SpendingChangeItem(
                        category_id=str(b.category_id),
                        category_name=b.category_name,
                        current_amount=b.actual_amount,
                        baseline_amount=base,
                        change_pct=chg_pct,
                        direction=direction,
                    )
                )

    spending_changes.sort(key=lambda x: abs(x.change_pct), reverse=True)

    return GuidanceResponse(
        insights=active_insights,
        summary=summary_stats,
        cashflow_strip=cashflow_strip,
        month_at_risk=month_at_risk[:6],
        spending_changes=spending_changes[:5],
        currency=ctx.primary_currency,
        as_of=ctx.today.isoformat(),
    )


async def record_guidance_feedback(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    insight_id: str,
    payload: GuidanceFeedbackCreate,
) -> GuidanceFeedback:
    """Record user feedback, snooze (7/30 days), or permanent dismissal."""
    stmt = select(GuidanceFeedback).where(
        GuidanceFeedback.workspace_id == workspace_id,
        GuidanceFeedback.insight_id == insight_id,
    )
    res = await session.execute(stmt)
    record = res.scalar_one_or_none()

    now_utc = datetime.now(timezone.utc)

    if not record:
        record = GuidanceFeedback(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            insight_id=insight_id,
            created_at=now_utc,
            updated_at=now_utc,
        )
        session.add(record)

    if payload.status:
        record.status = payload.status

    if payload.snooze_days:
        record.status = "snoozed"
        record.snoozed_until = now_utc + timedelta(days=payload.snooze_days)
    elif payload.status == "active":
        record.snoozed_until = None

    if payload.is_helpful is not None:
        record.is_helpful = payload.is_helpful

    if payload.action_taken:
        record.action_taken = payload.action_taken

    if payload.feedback_notes:
        record.feedback_notes = payload.feedback_notes

    record.updated_at = now_utc
    await session.commit()
    await session.refresh(record)
    return record


async def get_guidance_history(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[GuidanceHistoryItem]:
    """Retrieve history of user-interacted guidance items (dismissed, snoozed, acted-on)."""
    stmt = (
        select(GuidanceFeedback)
        .where(GuidanceFeedback.workspace_id == workspace_id)
        .order_by(GuidanceFeedback.updated_at.desc())
        .limit(50)
    )
    res = await session.execute(stmt)
    records = res.scalars().all()

    items = []
    for r in records:
        items.append(
            GuidanceHistoryItem(
                id=str(r.id),
                insight_id=r.insight_id,
                title=r.insight_id.replace("_", " ").title(),
                severity="info",
                status=r.status,
                snoozed_until=r.snoozed_until.isoformat() if r.snoozed_until else None,
                is_helpful=r.is_helpful,
                action_taken=r.action_taken,
                created_at=r.created_at.isoformat(),
                updated_at=r.updated_at.isoformat(),
            )
        )
    return items
