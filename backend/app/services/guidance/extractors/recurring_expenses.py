from datetime import timedelta
from decimal import Decimal
import uuid

from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def extract_recurring_signals(ctx: NormalizedGuidanceContext) -> list[RawSignal]:
    signals: list[RawSignal] = []
    month_key = f"{ctx.target_month.year:04d}_{ctx.target_month.month:02d}"

    # 1. Price increases (recurring cost creep)
    for r in ctx.recurring_items:
        if r.type == "debit" and r.price_increase_pct and r.price_increase_pct >= 5.0 and r.last_amount:
            inc_amount = r.amount - r.last_amount
            signals.append(
                RawSignal(
                    id=f"recurring_price_hike_{r.id}_{month_key}",
                    extractor_name="recurring_expenses",
                    signal_type="recurring_price_increase",
                    impact_amount=inc_amount,
                    urgency_days=30,
                    persistence_score=85.0,
                    confidence_score=95.0,
                    relevance_score=75.0,
                    title=f"Recurring price increase: {r.name} increased by {r.price_increase_pct:.0f}%",
                    summary=(
                        f"{r.name} increased from {r.last_amount} to {r.amount} (+{inc_amount}/cycle)."
                    ),
                    category_id=r.category_id,
                    category_name=r.category_name,
                    account_id=r.account_id,
                    account_name=r.account_name,
                    recurring_id=r.id,
                    metrics={
                        "current_amount": float(r.amount),
                        "previous_amount": float(r.last_amount),
                        "increase_amount": float(inc_amount),
                        "increase_pct": r.price_increase_pct,
                    },
                )
            )

    # 2. Missed regular payments
    for r in ctx.recurring_items:
        if r.type == "debit" and r.is_overdue:
            days_overdue = (ctx.today - r.next_occurrence).days if r.next_occurrence else 1
            signals.append(
                RawSignal(
                    id=f"recurring_missed_{r.id}_{month_key}",
                    extractor_name="recurring_expenses",
                    signal_type="recurring_missed_payment",
                    impact_amount=r.amount,
                    urgency_days=0,  # immediate
                    persistence_score=40.0,
                    confidence_score=90.0,
                    relevance_score=95.0,
                    title=f"Possible missed bill payment: {r.name}",
                    summary=(
                        f"{r.name} was scheduled for {r.next_occurrence} ({days_overdue} days ago) "
                        f"but no matching payment was detected."
                    ),
                    category_id=r.category_id,
                    category_name=r.category_name,
                    account_id=r.account_id,
                    account_name=r.account_name,
                    recurring_id=r.id,
                    metrics={
                        "amount": float(r.amount),
                        "due_date": str(r.next_occurrence),
                        "days_overdue": days_overdue,
                    },
                )
            )

    # 3. Upcoming Bill Cluster (next 7 days debit load)
    horizon_7d = ctx.today + timedelta(days=7)
    upcoming_bills = [
        r for r in ctx.recurring_items
        if r.type == "debit" and r.next_occurrence and ctx.today <= r.next_occurrence <= horizon_7d
    ]

    total_upcoming_debits = sum(b.amount for b in upcoming_bills)
    if total_upcoming_debits > Decimal("0.00") and ctx.liquid_balance > Decimal("0.00"):
        ratio = float(total_upcoming_debits / ctx.liquid_balance * 100)
        if ratio >= 40.0 or total_upcoming_debits > ctx.liquid_balance:
            signals.append(
                RawSignal(
                    id=f"recurring_bill_cluster_{month_key}",
                    extractor_name="recurring_expenses",
                    signal_type="recurring_bill_cluster",
                    impact_amount=total_upcoming_debits,
                    urgency_days=7,
                    persistence_score=50.0,
                    confidence_score=95.0,
                    relevance_score=90.0,
                    title="Heavy bill cluster due in the next 7 days",
                    summary=(
                        f"{len(upcoming_bills)} upcoming bills totaling {total_upcoming_debits} "
                        f"will take {ratio:.0f}% of your current liquid balance ({ctx.liquid_balance})."
                    ),
                    metrics={
                        "total_bills_amount": float(total_upcoming_debits),
                        "liquid_balance": float(ctx.liquid_balance),
                        "bill_count": len(upcoming_bills),
                        "drain_ratio_pct": round(ratio, 1),
                        "bill_names": [b.name for b in upcoming_bills],
                    },
                )
            )

    # 4. Subscription clean-up / audit
    subscriptions = [r for r in ctx.recurring_items if r.is_subscription and r.type == "debit"]
    sub_total = sum(s.amount for s in subscriptions)
    if len(subscriptions) >= 3 and sub_total >= Decimal("75.00"):
        signals.append(
            RawSignal(
                id=f"recurring_subs_audit_{month_key}",
                extractor_name="recurring_expenses",
                signal_type="recurring_subscription_audit",
                impact_amount=sub_total,
                urgency_days=30,
                persistence_score=80.0,
                confidence_score=85.0,
                relevance_score=60.0,
                title=f"Review active subscriptions ({len(subscriptions)} active, {sub_total}/mo)",
                summary=(
                    f"You have {len(subscriptions)} active recurring subscriptions consuming {sub_total} "
                    f"per month. An audit can identify idle or duplicate services."
                ),
                metrics={
                    "subscription_count": len(subscriptions),
                    "total_monthly_cost": float(sub_total),
                    "subscriptions": [{"name": s.name, "amount": float(s.amount)} for s in subscriptions],
                },
            )
        )

    return signals
