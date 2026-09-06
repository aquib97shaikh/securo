from decimal import Decimal

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_savings_rate_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    if ctx.monthly_income <= Decimal("0.00") or ctx.prior_monthly_income <= Decimal("0.00"):
        return signals

    cur_rate = ctx.savings_rate
    prior_rate = ctx.prior_savings_rate

    # 1. Savings rate decline
    if cur_rate < prior_rate - 5.0 and ctx.monthly_income > Decimal("0.00"):
        drop_pct = round(prior_rate - cur_rate, 1)

        # Calculate exact recovery action: how many dollars to reduce spending to restore prior savings rate
        target_expenses = ctx.monthly_income * (Decimal("1.0") - (Decimal(str(prior_rate)) / Decimal("100.0")))
        recovery_amount = max(Decimal("0.00"), ctx.monthly_expenses - target_expenses)

        signals.append(
            RawSignal(
                id=f"savings_rate_decline_{month_key}",
                extractor_name="savings_rate",
                signal_type="savings_rate_decline",
                impact_amount=recovery_amount,
                urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                persistence_score=50.0,
                confidence_score=95.0,
                relevance_score=85.0,
                title=f"Savings rate dropped to {cur_rate:.0f}% (down {drop_pct:.0f}% vs last month)",
                summary=(
                    f"Your savings rate is {cur_rate:.0f}% compared to {prior_rate:.0f}% last month. "
                    f"Trimming discretionary spend by {recovery_amount} will restore your baseline savings pace."
                ),
                metrics={
                    "current_savings_rate": cur_rate,
                    "prior_savings_rate": prior_rate,
                    "rate_drop_pct": drop_pct,
                    "recovery_amount": float(recovery_amount),
                    "current_income": float(ctx.monthly_income),
                    "current_expenses": float(ctx.monthly_expenses),
                },
            )
        )

    # 2. Savings rate surplus / improvement (positive signal with goal conversion action)
    elif cur_rate >= prior_rate + 8.0 and cur_rate > 10.0:
        surplus = max(Decimal("0.00"), ctx.monthly_income - ctx.monthly_expenses)
        improvement_pct = round(cur_rate - prior_rate, 1)

        signals.append(
            RawSignal(
                id=f"savings_rate_surplus_{month_key}",
                extractor_name="savings_rate",
                signal_type="savings_rate_surplus",
                impact_amount=surplus,
                urgency_days=30,
                persistence_score=40.0,
                confidence_score=90.0,
                relevance_score=70.0,
                title=f"Savings rate increased to {cur_rate:.0f}% (+{improvement_pct:.0f}%)",
                summary=(
                    f"Great momentum: you saved {surplus} ({cur_rate:.0f}% of income) this month. "
                    f"Consider routing this surplus directly toward your savings goals."
                ),
                metrics={
                    "current_savings_rate": cur_rate,
                    "prior_savings_rate": prior_rate,
                    "improvement_pct": improvement_pct,
                    "surplus_amount": float(surplus),
                },
            )
        )

    return signals
