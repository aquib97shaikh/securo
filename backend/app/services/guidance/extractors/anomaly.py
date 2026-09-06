import math
from decimal import Decimal
import uuid

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_anomaly_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    # Use 90-day debit transactions as statistical baseline
    baseline_amounts = [float(t.amount) for t in ctx.history_90d_txs if t.type == "debit" and t.amount > Decimal("1.00")]

    if len(baseline_amounts) < 15:
        return signals

    mean = sum(baseline_amounts) / len(baseline_amounts)
    variance = sum((x - mean) ** 2 for x in baseline_amounts) / len(baseline_amounts)
    stddev = math.sqrt(variance)

    if stddev < 5.0:
        return signals

    # Check current month transactions for statistical outliers (z-score > 2.5)
    for t in ctx.current_month_txs:
        if t.type != "debit" or t.is_recurring:
            continue

        val = float(t.amount)
        z_score = (val - mean) / stddev

        if z_score >= 2.5 and t.amount >= Decimal("150.00"):
            signals.append(
                RawSignal(
                    id=f"anomaly_spike_{t.id}_{month_key}",
                    extractor_name="anomaly",
                    signal_type="statistical_spending_anomaly",
                    impact_amount=t.amount,
                    urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                    persistence_score=20.0,  # one-off by definition
                    confidence_score=90.0,
                    relevance_score=75.0,
                    title=f"Unusually large transaction: {t.payee_name} ({t.amount})",
                    summary=(
                        f"This {t.amount} expense is {z_score:.1f} standard deviations above your "
                        f"90-day average transaction size ({round(mean, 2)})."
                    ),
                    category_id=t.category_id,
                    category_name=t.category_name,
                    account_id=t.account_id,
                    account_name=t.account_name,
                    transaction_ids=[t.id],
                    metrics={
                        "transaction_amount": val,
                        "mean_amount": round(mean, 2),
                        "stddev": round(stddev, 2),
                        "z_score": round(z_score, 2),
                    },
                )
            )

    return signals
