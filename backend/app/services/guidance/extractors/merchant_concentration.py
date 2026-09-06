from collections import defaultdict
from decimal import Decimal
import uuid

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_merchant_concentration_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    # Filter to current month discretionary debit transactions
    disc_txs = [t for t in ctx.current_month_txs if t.type == "debit" and t.is_discretionary]
    total_disc_spend = sum(t.amount for t in disc_txs)

    if total_disc_spend < Decimal("150.00") or not disc_txs:
        return signals

    merchant_spend: dict[str, Decimal] = defaultdict(Decimal)
    merchant_tx_ids: dict[str, list[uuid.UUID]] = defaultdict(list)
    merchant_categories: dict[str, str] = {}

    for t in disc_txs:
        m_name = (t.payee_name or "Unknown").strip()
        merchant_spend[m_name] += t.amount
        merchant_tx_ids[m_name].append(t.id)
        if m_name not in merchant_categories:
            merchant_categories[m_name] = t.category_name

    # Sort merchants by spend descending
    sorted_merchants = sorted(merchant_spend.items(), key=lambda x: x[1], reverse=True)
    if not sorted_merchants:
        return signals

    top_merchant, top_spend = sorted_merchants[0]
    top_pct = round(float(top_spend / total_disc_spend * 100), 1)

    # 1. Single Merchant Concentration: > 35% of all discretionary spend
    if top_pct >= 35.0 and top_spend >= Decimal("100.00"):
        cat_name = merchant_categories.get(top_merchant, "Discretionary")
        tx_ids = merchant_tx_ids[top_merchant]

        signals.append(
            RawSignal(
                id=f"merchant_concentration_{abs(hash(top_merchant)) % 100000}_{month_key}",
                extractor_name="merchant_concentration",
                signal_type="merchant_concentration_high",
                impact_amount=top_spend,
                urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                persistence_score=55.0,
                confidence_score=90.0,
                relevance_score=65.0,
                title=f"High merchant concentration: {top_merchant} dominates {top_pct:.0f}% of discretionary spend",
                summary=(
                    f"You spent {top_spend} at {top_merchant} ({len(tx_ids)} transactions), representing "
                    f"{top_pct:.0f}% of your total discretionary spend ({total_disc_spend}) this month."
                ),
                category_name=cat_name,
                transaction_ids=tx_ids,
                metrics={
                    "merchant_name": top_merchant,
                    "merchant_spend": float(top_spend),
                    "total_discretionary_spend": float(total_disc_spend),
                    "concentration_pct": top_pct,
                    "transaction_count": len(tx_ids),
                },
            )
        )

    return signals
