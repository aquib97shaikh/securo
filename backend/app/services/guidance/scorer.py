from decimal import Decimal
from typing import Tuple

from app.schemas.guidance import ScoreBreakdown
from app.services.guidance.extractors.base import RawSignal
from app.services.guidance.normalizer import NormalizedGuidanceContext


def calculate_severity_score(
    signal: RawSignal, ctx: NormalizedGuidanceContext
) -> Tuple[float, str, ScoreBreakdown]:
    """Calculate 100-point deterministic score:

    score = 0.30*I + 0.25*U + 0.20*P + 0.15*C + 0.10*R

    Returns:
        (total_score, severity_tier, ScoreBreakdown)
    """

    # 1. Impact (I): 0 to 100
    # Financial scale relative to monthly income or standard baseline
    income_base = ctx.monthly_income if ctx.monthly_income > Decimal("0.00") else Decimal("2000.00")
    if signal.signal_type in ("cashflow_shortfall", "cashflow_safety_buffer_breached"):
        # Shortfalls are inherently high impact
        raw_i = 75.0 + float((signal.impact_amount or Decimal("0.00")) / income_base) * 40.0
    elif signal.impact_amount:
        ratio = float(signal.impact_amount / income_base) * 100.0
        raw_i = min(100.0, max(15.0, ratio * 3.0))
    else:
        raw_i = 30.0
    impact = min(100.0, max(0.0, raw_i))

    # 2. Urgency (U): 0 to 100
    if signal.urgency_days is not None:
        d = signal.urgency_days
        if d <= 0:
            urgency = 100.0
        elif d <= 3:
            urgency = 95.0
        elif d <= 7:
            urgency = 85.0
        elif d <= 14:
            urgency = 70.0
        elif d <= 21:
            urgency = 55.0
        elif d <= 30:
            urgency = 40.0
        else:
            urgency = 25.0
    else:
        urgency = 30.0

    # 3. Persistence (P): 0 to 100
    persistence = min(100.0, max(0.0, signal.persistence_score))

    # 4. Confidence (C): 0 to 100
    confidence = min(100.0, max(0.0, signal.confidence_score))

    # 5. Relevance (R): 0 to 100
    relevance = min(100.0, max(0.0, signal.relevance_score))

    # Calculate deterministic weighted total
    total = (
        0.30 * impact
        + 0.25 * urgency
        + 0.20 * persistence
        + 0.15 * confidence
        + 0.10 * relevance
    )
    total = round(min(100.0, max(0.0, total)), 1)

    # Map to canonical severity tiers
    if total >= 80.0:
        tier = "urgent"
    elif total >= 60.0:
        tier = "action_needed"
    elif total >= 40.0:
        tier = "watch"
    else:
        tier = "informational"

    breakdown = ScoreBreakdown(
        impact=round(impact, 1),
        urgency=round(urgency, 1),
        persistence=round(persistence, 1),
        confidence=round(confidence, 1),
        relevance=round(relevance, 1),
        total_score=total,
    )

    return total, tier, breakdown
