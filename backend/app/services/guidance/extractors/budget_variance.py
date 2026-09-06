from decimal import Decimal
import uuid

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_budget_variance_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    for b in ctx.budgets:
        if b.budget_amount <= 0:
            continue

        txs = [t for t in ctx.current_month_txs if t.category_id == b.category_id]
        tx_ids = [t.id for t in txs]

        # 1. Actual overspend
        if b.actual_amount > b.budget_amount:
            overspend = b.actual_amount - b.budget_amount
            pct_over = round(float(overspend / b.budget_amount * 100), 1)

            # Persistence: did it exceed last month as well?
            repeated = b.prev_month_amount > b.budget_amount
            persistence = 85.0 if repeated else 40.0
            relevance = 90.0 if not b.is_discretionary else 70.0
            days_left = max(1, ctx.days_in_month - ctx.days_elapsed)

            signals.append(
                RawSignal(
                    id=f"budget_overspend_{b.category_id}_{month_key}",
                    extractor_name="budget_variance",
                    signal_type="budget_overspend",
                    impact_amount=overspend,
                    urgency_days=days_left,
                    persistence_score=persistence,
                    confidence_score=95.0,
                    relevance_score=relevance,
                    title=f"{b.category_name} is over budget by {pct_over:.0f}%",
                    summary=(
                        f"You have spent {b.actual_amount} against a {b.budget_amount} budget, "
                        f"exceeding your cap by {overspend}."
                    ),
                    category_id=b.category_id,
                    category_name=b.category_name,
                    transaction_ids=tx_ids,
                    metrics={
                        "budget_amount": float(b.budget_amount),
                        "actual_amount": float(b.actual_amount),
                        "overspend_amount": float(overspend),
                        "pct_over": pct_over,
                        "repeated": repeated,
                    },
                )
            )

        # 2. Projected overspend (early warning)
        elif b.projected_amount > b.budget_amount * Decimal("1.15") and ctx.days_elapsed < ctx.days_in_month - 3:
            projected_over = b.projected_amount - b.budget_amount
            pct_proj_over = round(float(projected_over / b.budget_amount * 100), 1)
            days_left = max(1, ctx.days_in_month - ctx.days_elapsed)

            signals.append(
                RawSignal(
                    id=f"budget_projected_overspend_{b.category_id}_{month_key}",
                    extractor_name="budget_variance",
                    signal_type="budget_projected_overspend",
                    impact_amount=projected_over,
                    urgency_days=days_left,
                    persistence_score=50.0,
                    confidence_score=85.0,
                    relevance_score=75.0,
                    title=f"{b.category_name} projected to exceed budget by {pct_proj_over:.0f}%",
                    summary=(
                        f"At current spending rate, {b.category_name} is on track to reach "
                        f"{b.projected_amount} ({pct_proj_over:.0f}% over budget)."
                    ),
                    category_id=b.category_id,
                    category_name=b.category_name,
                    transaction_ids=tx_ids,
                    metrics={
                        "budget_amount": float(b.budget_amount),
                        "projected_amount": float(b.projected_amount),
                        "projected_overspend": float(projected_over),
                        "pct_proj_over": pct_proj_over,
                    },
                )
            )

        # 3. Budget exhausted early (first half of month)
        if ctx.days_elapsed <= 15 and b.percentage_used >= 90.0:
            signals.append(
                RawSignal(
                    id=f"budget_exhausted_early_{b.category_id}_{month_key}",
                    extractor_name="budget_variance",
                    signal_type="budget_exhausted_early",
                    impact_amount=b.actual_amount,
                    urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                    persistence_score=60.0,
                    confidence_score=90.0,
                    relevance_score=80.0,
                    title=f"{b.category_name} budget nearly exhausted early in the month",
                    summary=(
                        f"You've consumed {b.percentage_used:.0f}% of your {b.category_name} budget "
                        f"by day {ctx.days_elapsed}."
                    ),
                    category_id=b.category_id,
                    category_name=b.category_name,
                    transaction_ids=tx_ids,
                    metrics={
                        "budget_amount": float(b.budget_amount),
                        "actual_amount": float(b.actual_amount),
                        "pct_used": b.percentage_used,
                        "day_of_month": ctx.days_elapsed,
                    },
                )
            )

        # 4. Under-budget surplus opportunity (for reallocation)
        elif (
            ctx.days_elapsed >= 20
            and b.percentage_used < 50.0
            and (b.budget_amount - b.actual_amount) >= Decimal("100.00")
        ):
            surplus = b.budget_amount - b.actual_amount
            signals.append(
                RawSignal(
                    id=f"budget_surplus_{b.category_id}_{month_key}",
                    extractor_name="budget_variance",
                    signal_type="budget_surplus",
                    impact_amount=surplus,
                    urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                    persistence_score=30.0,
                    confidence_score=90.0,
                    relevance_score=60.0,
                    title=f"Reallocation opportunity: {b.category_name} has unspent budget",
                    summary=(
                        f"{b.category_name} is using only {b.percentage_used:.0f}% of budget, "
                        f"leaving {surplus} that could be reallocated or saved."
                    ),
                    category_id=b.category_id,
                    category_name=b.category_name,
                    transaction_ids=tx_ids,
                    metrics={
                        "budget_amount": float(b.budget_amount),
                        "actual_amount": float(b.actual_amount),
                        "surplus_amount": float(surplus),
                        "pct_used": b.percentage_used,
                    },
                )
            )

    return signals
