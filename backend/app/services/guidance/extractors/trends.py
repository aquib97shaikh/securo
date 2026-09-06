from collections import defaultdict
from decimal import Decimal
import uuid

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_trend_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    # Group current month expenses by category
    cur_cat_spend: dict[uuid.UUID, Decimal] = defaultdict(Decimal)
    cur_cat_names: dict[uuid.UUID, str] = {}
    cur_cat_txs: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)

    for t in ctx.current_month_txs:
        if t.type == "debit" and t.category_id:
            cur_cat_spend[t.category_id] += t.amount
            cur_cat_names[t.category_id] = t.category_name
            cur_cat_txs[t.category_id].append(t.id)

    # Group prior month expenses by category
    prior_cat_spend: dict[uuid.UUID, Decimal] = defaultdict(Decimal)
    for t in ctx.prior_month_txs:
        if t.type == "debit" and t.category_id:
            prior_cat_spend[t.category_id] += t.amount

    # Group 90d expenses by category and compute 90-day monthly average
    hist_90d_spend: dict[uuid.UUID, Decimal] = defaultdict(Decimal)
    for t in ctx.history_90d_txs:
        if t.type == "debit" and t.category_id:
            hist_90d_spend[t.category_id] += t.amount

    avg_90d_cat_spend: dict[uuid.UUID, Decimal] = {
        cid: round(amt / Decimal("3.0"), 2) for cid, amt in hist_90d_spend.items()
    }

    # Analyze each category
    for cat_id, cur_amt in cur_cat_spend.items():
        cat_name = cur_cat_names.get(cat_id, "Category")
        prev_amt = prior_cat_spend.get(cat_id, Decimal("0.00"))
        baseline_90d = avg_90d_cat_spend.get(cat_id, Decimal("0.00"))
        tx_ids = cur_cat_txs[cat_id]

        # 1. MoM Surge: spend >= 1.5x prior month and increase >= 50.00
        if prev_amt > 0 and cur_amt >= prev_amt * Decimal("1.5") and (cur_amt - prev_amt) >= Decimal("50.00"):
            increase = cur_amt - prev_amt
            pct_inc = round(float(increase / prev_amt * 100), 1)
            signals.append(
                RawSignal(
                    id=f"trend_surge_mom_{cat_id}_{month_key}",
                    extractor_name="trends",
                    signal_type="trend_surge_mom",
                    impact_amount=increase,
                    urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                    persistence_score=40.0,
                    confidence_score=90.0,
                    relevance_score=70.0,
                    title=f"{cat_name} jumped {pct_inc:.0f}% vs last month",
                    summary=(
                        f"You spent {cur_amt} in {cat_name} this month, up from {prev_amt} "
                        f"last month (+{increase})."
                    ),
                    category_id=cat_id,
                    category_name=cat_name,
                    transaction_ids=tx_ids,
                    metrics={
                        "current_amount": float(cur_amt),
                        "prior_amount": float(prev_amt),
                        "increase_amount": float(increase),
                        "pct_increase": pct_inc,
                    },
                )
            )

        # 2. 90-day Baseline Deviation: pacing > 35% above 90-day average
        if baseline_90d > 0 and ctx.days_elapsed > 10:
            # Projected monthly amount
            projected = round((cur_amt / Decimal(str(ctx.days_elapsed))) * Decimal(str(ctx.days_in_month)), 2)
            if projected >= baseline_90d * Decimal("1.35") and (projected - baseline_90d) >= Decimal("60.00"):
                diff = projected - baseline_90d
                pct_above = round(float(diff / baseline_90d * 100), 1)
                signals.append(
                    RawSignal(
                        id=f"trend_surge_90d_{cat_id}_{month_key}",
                        extractor_name="trends",
                        signal_type="trend_surge_90d",
                        impact_amount=diff,
                        urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                        persistence_score=75.0,
                        confidence_score=90.0,
                        relevance_score=75.0,
                        title=f"{cat_name} is running {pct_above:.0f}% above 90-day average",
                        summary=(
                            f"Projected {cat_name} spend ({projected}) significantly exceeds your "
                            f"3-month baseline average of {baseline_90d}."
                        ),
                        category_id=cat_id,
                        category_name=cat_name,
                        transaction_ids=tx_ids,
                        metrics={
                            "current_amount": float(cur_amt),
                            "projected_amount": float(projected),
                            "baseline_90d": float(baseline_90d),
                            "pct_above_baseline": pct_above,
                        },
                    )
                )

        # 3. Category Drift: category share of total expenses expanded by > 10%
        if ctx.monthly_expenses > 0 and ctx.avg_90d_monthly_expenses > 0:
            cur_share = float(cur_amt / ctx.monthly_expenses * 100)
            baseline_share = float(baseline_90d / ctx.avg_90d_monthly_expenses * 100) if baseline_90d > 0 else 0.0

            if cur_share >= baseline_share + 10.0 and cur_amt >= Decimal("100.00"):
                signals.append(
                    RawSignal(
                        id=f"trend_drift_{cat_id}_{month_key}",
                        extractor_name="trends",
                        signal_type="trend_category_drift",
                        impact_amount=cur_amt,
                        urgency_days=max(1, ctx.days_in_month - ctx.days_elapsed),
                        persistence_score=60.0,
                        confidence_score=85.0,
                        relevance_score=65.0,
                        title=f"{cat_name} is consuming a growing share of your budget",
                        summary=(
                            f"{cat_name} accounts for {cur_share:.0f}% of total spending this month, "
                            f"compared to your historical baseline of {baseline_share:.0f}%."
                        ),
                        category_id=cat_id,
                        category_name=cat_name,
                        transaction_ids=tx_ids,
                        metrics={
                            "current_share_pct": round(cur_share, 1),
                            "baseline_share_pct": round(baseline_share, 1),
                            "current_amount": float(cur_amt),
                        },
                    )
                )

    return signals
