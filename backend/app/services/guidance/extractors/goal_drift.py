from decimal import Decimal
import uuid

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_goal_drift_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    for g in ctx.goals:
        if g.target_amount <= Decimal("0.00") or g.current_amount >= g.target_amount:
            continue

        shortfall = g.target_amount - g.current_amount

        # 1. Overdue Goal
        if g.target_date and g.target_date < ctx.today:
            days_overdue = (ctx.today - g.target_date).days
            signals.append(
                RawSignal(
                    id=f"goal_overdue_{g.id}_{month_key}",
                    extractor_name="goal_drift",
                    signal_type="goal_overdue",
                    impact_amount=shortfall,
                    urgency_days=0,
                    persistence_score=80.0,
                    confidence_score=95.0,
                    relevance_score=90.0,
                    title=f"Goal target date passed: {g.name}",
                    summary=(
                        f"Your target date for '{g.name}' was {g.target_date} ({days_overdue} days ago). "
                        f"{shortfall} remains to reach your {g.target_amount} target."
                    ),
                    goal_id=g.id,
                    metrics={
                        "target_amount": float(g.target_amount),
                        "current_amount": float(g.current_amount),
                        "shortfall_amount": float(shortfall),
                        "target_date": str(g.target_date),
                        "days_overdue": days_overdue,
                    },
                )
            )

        # 2. Behind schedule pace
        elif g.on_track in ("behind", "off_track") or (
            g.monthly_target_contribution > Decimal("0.00")
            and g.target_date
            and (g.target_date - ctx.today).days <= 180
        ):
            urgency_days = (g.target_date - ctx.today).days if g.target_date else 90
            signals.append(
                RawSignal(
                    id=f"goal_behind_{g.id}_{month_key}",
                    extractor_name="goal_drift",
                    signal_type="goal_behind_schedule",
                    impact_amount=g.monthly_target_contribution,
                    urgency_days=max(1, urgency_days),
                    persistence_score=70.0,
                    confidence_score=90.0,
                    relevance_score=85.0,
                    title=f"Goal '{g.name}' is behind planned schedule",
                    summary=(
                        f"At current progress ({g.current_amount} of {g.target_amount}), you need to contribute "
                        f"{g.monthly_target_contribution}/month to reach your target by {g.target_date}."
                    ),
                    goal_id=g.id,
                    metrics={
                        "target_amount": float(g.target_amount),
                        "current_amount": float(g.current_amount),
                        "shortfall_amount": float(shortfall),
                        "monthly_needed": float(g.monthly_target_contribution),
                        "target_date": str(g.target_date) if g.target_date else None,
                        "on_track": g.on_track,
                    },
                )
            )

    return signals
