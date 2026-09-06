from collections import defaultdict
from decimal import Decimal
import uuid

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_behavioral_pattern_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    disc_txs = [t for t in ctx.current_month_txs if t.type == "debit" and t.is_discretionary]
    total_disc_spend = sum(t.amount for t in disc_txs)

    # 1. Weekend Spending Spikes (> 45% of discretionary on Saturday/Sunday)
    if total_disc_spend >= Decimal("200.00"):
        weekend_txs = [t for t in disc_txs if t.date.weekday() in (5, 6)]
        weekend_spend = sum(t.amount for t in weekend_txs)
        weekend_pct = round(float(weekend_spend / total_disc_spend * 100), 1)

        if weekend_pct >= 45.0:
            signals.append(
                RawSignal(
                    id=f"behavior_weekend_spike_{month_key}",
                    extractor_name="behavioral_patterns",
                    signal_type="behavior_weekend_spike",
                    impact_amount=weekend_spend,
                    urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                    persistence_score=60.0,
                    confidence_score=85.0,
                    relevance_score=60.0,
                    title=f"Weekend spending spike: {weekend_pct:.0f}% of discretionary spend on weekends",
                    summary=(
                        f"You spent {weekend_spend} across {len(weekend_txs)} weekend purchases, accounting "
                        f"for {weekend_pct:.0f}% of your monthly discretionary budget."
                    ),
                    transaction_ids=[t.id for t in weekend_txs],
                    metrics={
                        "weekend_spend": float(weekend_spend),
                        "total_discretionary_spend": float(total_disc_spend),
                        "weekend_pct": weekend_pct,
                        "weekend_tx_count": len(weekend_txs),
                    },
                )
            )

    # 2. Food delivery / Takeout concentration
    delivery_keywords = {"ifood", "uber eats", "doordash", "rappi", "grubhub", "delivery", "takeout"}
    delivery_txs = [
        t for t in ctx.current_month_txs
        if t.type == "debit" and any(k in (t.payee_name or "").lower() for k in delivery_keywords)
    ]
    delivery_spend = sum(t.amount for t in delivery_txs)

    if len(delivery_txs) >= 4 and delivery_spend >= Decimal("150.00"):
        signals.append(
            RawSignal(
                id=f"behavior_delivery_spike_{month_key}",
                extractor_name="behavioral_patterns",
                signal_type="behavior_delivery_spike",
                impact_amount=delivery_spend,
                urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                persistence_score=70.0,
                confidence_score=90.0,
                relevance_score=65.0,
                title=f"Frequent food delivery: {delivery_spend} across {len(delivery_txs)} orders",
                summary=(
                    f"Food delivery orders accumulated to {delivery_spend} this month across {len(delivery_txs)} transactions. "
                    f"Setting a monthly guardrail could free up significant cash."
                ),
                transaction_ids=[t.id for t in delivery_txs],
                metrics={
                    "delivery_spend": float(delivery_spend),
                    "order_count": len(delivery_txs),
                    "avg_order_size": float(round(delivery_spend / len(delivery_txs), 2)),
                },
            )
        )

    # 3. Payday splurge (surge in spending within 3 days of an income deposit)
    income_txs = [t for t in ctx.current_month_txs if t.type == "credit" and t.amount >= Decimal("500.00")]
    for inc in income_txs:
        # Transactions in [inc.date, inc.date + 3 days]
        window_end = inc.date + (inc.date.replace(day=min(inc.date.day + 3, ctx.days_in_month)) - inc.date)
        post_income_txs = [
            t for t in disc_txs
            if inc.date <= t.date <= window_end
        ]
        post_income_spend = sum(t.amount for t in post_income_txs)
        if post_income_spend >= inc.amount * Decimal("0.30") and post_income_spend >= Decimal("200.00"):
            splurge_pct = round(float(post_income_spend / inc.amount * 100), 1)
            signals.append(
                RawSignal(
                    id=f"behavior_payday_splurge_{inc.id}_{month_key}",
                    extractor_name="behavioral_patterns",
                    signal_type="behavior_payday_splurge",
                    impact_amount=post_income_spend,
                    urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                    persistence_score=50.0,
                    confidence_score=85.0,
                    relevance_score=70.0,
                    title=f"Post-payday surge: {splurge_pct:.0f}% of income spent within 3 days",
                    summary=(
                        f"After your {inc.amount} deposit on {inc.date}, you spent {post_income_spend} "
                        f"on discretionary purchases in 3 days."
                    ),
                    transaction_ids=[t.id for t in post_income_txs],
                    metrics={
                        "income_amount": float(inc.amount),
                        "post_income_spend": float(post_income_spend),
                        "splurge_pct": splurge_pct,
                    },
                )
            )

    return signals
