from datetime import datetime, timezone
from decimal import Decimal
import re
from typing import Any, Optional

from app.schemas.guidance import (
    EvidenceBudget,
    EvidenceData,
    EvidenceForecastPoint,
    EvidenceGoal,
    EvidenceRecurring,
    EvidenceTransaction,
    GuidanceInsight,
    RecommendedAction,
    ScoreBreakdown,
)
from app.services.guidance.catalog import get_rule_for_signal
from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def _render_template(template: str, params: dict[str, Any]) -> str:
    """Safely format string template with available params."""
    def replacer(match):
        key = match.group(1)
        val = params.get(key)
        if val is None:
            return match.group(0)
        if isinstance(val, float):
            return f"{val:.1f}" if val != int(val) else f"{int(val)}"
        return str(val)

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", replacer, template)


def build_explainable_insight(
    signal: RawSignal,
    score: float,
    severity: str,
    breakdown: ScoreBreakdown,
    ctx: NormalizedGuidanceContext,
) -> GuidanceInsight:
    """Build canonical 5-point explainable guidance insight."""
    rule = get_rule_for_signal(signal.signal_type)

    # Build format parameters from signal metrics and context
    params: dict[str, Any] = {
        "category_name": signal.category_name or "Category",
        "currency": ctx.primary_currency,
        "days_elapsed": ctx.days_elapsed,
        "days_in_month": ctx.days_in_month,
        "days_left": max(1, ctx.days_in_month - ctx.days_elapsed),
        "liquid_balance": ctx.liquid_balance,
        "monthly_income": ctx.monthly_income,
        "monthly_expenses": ctx.monthly_expenses,
        "weekly_guardrail": (
            round((signal.impact_amount or Decimal("100.00")) / Decimal("2.0"), 2)
        ),
        "weekend_budget": (
            round((signal.impact_amount or Decimal("100.00")) * Decimal("0.70"), 2)
        ),
    }
    params.update(signal.metrics)

    # 1. What Happened?
    what_happened = signal.summary

    # 2. Why Does It Matter?
    why_it_matters = _render_template(rule.get("why_template", ""), params)

    # 3. How Was It Calculated?
    how_calculated = _render_template(rule.get("how_template", ""), params)

    # 4. What Can I Do Next?
    next_action_text = _render_template(rule.get("next_action_template", ""), params)

    # 5. Supporting Evidence
    # Transactions
    ev_txs: list[EvidenceTransaction] = []
    if signal.transaction_ids:
        matching_txs = [t for t in ctx.current_month_txs if t.id in signal.transaction_ids]
        # Fallback to 90d history if not in current month
        if not matching_txs:
            matching_txs = [t for t in ctx.history_90d_txs if t.id in signal.transaction_ids]

        for t in matching_txs[:8]:  # Top 8 supporting transactions
            ev_txs.append(
                EvidenceTransaction(
                    id=str(t.id),
                    date=str(t.date),
                    description=t.payee_name,
                    amount=t.amount,
                    category_name=t.category_name,
                    account_name=t.account_name,
                )
            )

    # Budget evidence
    ev_budget: Optional[EvidenceBudget] = None
    if signal.category_id:
        matching_b = next((b for b in ctx.budgets if b.category_id == signal.category_id), None)
        if matching_b:
            ev_budget = EvidenceBudget(
                category_id=str(matching_b.category_id),
                category_name=matching_b.category_name,
                budget_amount=matching_b.budget_amount,
                actual_amount=matching_b.actual_amount,
                variance=matching_b.variance,
                pct_used=matching_b.percentage_used,
            )

    # Goal evidence
    ev_goal: Optional[EvidenceGoal] = None
    if signal.goal_id:
        matching_g = next((g for g in ctx.goals if g.id == signal.goal_id), None)
        if matching_g:
            ev_goal = EvidenceGoal(
                goal_id=str(matching_g.id),
                name=matching_g.name,
                target_amount=matching_g.target_amount,
                current_amount=matching_g.current_amount,
                target_date=str(matching_g.target_date) if matching_g.target_date else None,
                on_track=matching_g.on_track,
                monthly_needed=matching_g.monthly_target_contribution,
            )

    # Recurring evidence
    ev_rec: Optional[EvidenceRecurring] = None
    if signal.recurring_id:
        matching_r = next((r for r in ctx.recurring_items if r.id == signal.recurring_id), None)
        if matching_r:
            ev_rec = EvidenceRecurring(
                recurring_id=str(matching_r.id),
                name=matching_r.name,
                amount=matching_r.amount,
                frequency=matching_r.frequency,
                next_date=str(matching_r.next_occurrence) if matching_r.next_occurrence else None,
                previous_amount=matching_r.last_amount,
                increase_pct=matching_r.price_increase_pct,
            )

    # Forecast points evidence (if shortfall or cashflow related)
    ev_forecast: list[EvidenceForecastPoint] = []
    if "cashflow" in signal.signal_type or "shortfall" in signal.signal_type:
        for day in ctx.cashflow_30d[:14]:  # 14 days snapshot
            ev_forecast.append(
                EvidenceForecastPoint(
                    date=str(day.date),
                    projected_balance=day.ending_balance,
                    net_change=day.inflows - day.outflows,
                    events=day.events,
                    has_shortfall=day.has_shortfall,
                )
            )

    evidence = EvidenceData(
        transactions=ev_txs,
        budget=ev_budget,
        goal=ev_goal,
        recurring=ev_rec,
        forecast_points=ev_forecast,
        metrics=signal.metrics,
    )

    action_type = rule.get("action_type", "review")
    action = RecommendedAction(
        type=action_type,
        label=rule.get("action_label", "Review details"),
        url=rule.get("action_url", "/dashboard"),
        payload={
            "action_type": action_type,
            "signal_id": signal.id,
            "category_id": str(signal.category_id) if signal.category_id else None,
            "goal_id": str(signal.goal_id) if signal.goal_id else None,
            "recurring_id": str(signal.recurring_id) if signal.recurring_id else None,
            "suggested_amount": float(signal.impact_amount) if signal.impact_amount else None,
        },
    )

    now_iso = datetime.now(timezone.utc).isoformat()

    return GuidanceInsight(
        id=signal.id,
        signal_type=signal.signal_type,
        family=rule.get("family", "budget_control"),
        severity=severity,
        score=score,
        score_breakdown=breakdown,
        title=signal.title,
        one_line_explanation=signal.summary,
        impact_amount=signal.impact_amount,
        currency=ctx.primary_currency,
        what_happened=what_happened,
        why_it_matters=why_it_matters,
        how_calculated=how_calculated,
        next_action=next_action_text,
        action=action,
        evidence=evidence,
        created_at=now_iso,
    )
