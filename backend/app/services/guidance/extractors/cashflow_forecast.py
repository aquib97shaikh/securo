from datetime import date
from decimal import Decimal

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_cashflow_forecast_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    # 1. Projected Cash Shortfall (balance < 0)
    if ctx.projected_shortfall_day and ctx.min_projected_balance < Decimal("0.00"):
        days_to_shortfall = (ctx.projected_shortfall_day - ctx.today).days
        shortfall_amt = abs(ctx.min_projected_balance)

        # High urgency if within 14 days
        urgency = 100.0 if days_to_shortfall <= 7 else (90.0 if days_to_shortfall <= 14 else 75.0)

        signals.append(
            RawSignal(
                id=f"cashflow_shortfall_{month_key}",
                extractor_name="cashflow_forecast",
                signal_type="cashflow_shortfall",
                impact_amount=shortfall_amt,
                urgency_days=days_to_shortfall,
                persistence_score=70.0,
                confidence_score=95.0,
                relevance_score=100.0,
                title=f"Cash shortfall projected in {days_to_shortfall} days",
                summary=(
                    f"Based on scheduled bills and recurring outflows, your liquid cash is projected "
                    f"to dip negative by {shortfall_amt} around {ctx.projected_shortfall_day}."
                ),
                metrics={
                    "shortfall_date": str(ctx.projected_shortfall_day),
                    "days_to_shortfall": days_to_shortfall,
                    "min_projected_balance": float(ctx.min_projected_balance),
                    "shortfall_amount": float(shortfall_amt),
                    "current_liquid_balance": float(ctx.liquid_balance),
                },
            )
        )

    # 2. Safety Buffer Breach (balance dips below user safety buffer, but above 0)
    elif (
        ctx.safety_buffer > Decimal("0.00")
        and ctx.min_projected_balance < ctx.safety_buffer
        and ctx.projected_shortfall_day
    ):
        days_to_breach = (ctx.projected_shortfall_day - ctx.today).days
        buffer_deficit = ctx.safety_buffer - ctx.min_projected_balance

        signals.append(
            RawSignal(
                id=f"cashflow_buffer_breach_{month_key}",
                extractor_name="cashflow_forecast",
                signal_type="cashflow_safety_buffer_breached",
                impact_amount=buffer_deficit,
                urgency_days=days_to_breach,
                persistence_score=50.0,
                confidence_score=90.0,
                relevance_score=85.0,
                title=f"Balance projected to breach safety buffer in {days_to_breach} days",
                summary=(
                    f"Projected balance will drop to {ctx.min_projected_balance}, below your "
                    f"{ctx.safety_buffer} emergency threshold around {ctx.projected_shortfall_day}."
                ),
                metrics={
                    "breach_date": str(ctx.projected_shortfall_day),
                    "days_to_breach": days_to_breach,
                    "safety_buffer": float(ctx.safety_buffer),
                    "min_projected_balance": float(ctx.min_projected_balance),
                    "buffer_deficit": float(buffer_deficit),
                },
            )
        )

    # 3. Low Balance Before Next Income
    # Find next scheduled income event
    next_income_day = None
    next_income_amt = Decimal("0.00")
    for day in ctx.cashflow_30d:
        if day.inflows > Decimal("0.00"):
            next_income_day = day.date
            next_income_amt = day.inflows
            break

    if next_income_day:
        days_to_income = (next_income_day - ctx.today).days
        # Find minimum balance before that income day
        min_bal_before_income = min(
            (d.ending_balance for d in ctx.cashflow_30d if d.date <= next_income_day),
            default=ctx.liquid_balance
        )
        if (
            min_bal_before_income > Decimal("0.00")
            and min_bal_before_income < Decimal("150.00")
            and days_to_income >= 3
        ):
            signals.append(
                RawSignal(
                    id=f"cashflow_low_before_income_{month_key}",
                    extractor_name="cashflow_forecast",
                    signal_type="cashflow_low_balance_before_income",
                    impact_amount=min_bal_before_income,
                    urgency_days=days_to_income,
                    persistence_score=40.0,
                    confidence_score=90.0,
                    relevance_score=85.0,
                    title=f"Tight balance ({min_bal_before_income}) before next income on {next_income_day}",
                    summary=(
                        f"Your available buffer will drop to {min_bal_before_income} over the next "
                        f"{days_to_income} days before your next expected deposit ({next_income_amt})."
                    ),
                    metrics={
                        "min_balance_before_income": float(min_bal_before_income),
                        "next_income_date": str(next_income_day),
                        "days_to_income": days_to_income,
                        "next_income_amount": float(next_income_amt),
                    },
                )
            )

    return signals
