from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional
import uuid

from app.services.guidance.normalizer import NormalizedGuidanceContext


@dataclass
class RawSignal:
    id: str
    extractor_name: str
    signal_type: str
    impact_amount: Optional[Decimal]
    urgency_days: Optional[int]
    persistence_score: float  # 0 to 100
    confidence_score: float  # 0 to 100
    relevance_score: float  # 0 to 100
    title: str
    summary: str
    category_id: Optional[uuid.UUID] = None
    category_name: Optional[str] = None
    account_id: Optional[uuid.UUID] = None
    account_name: Optional[str] = None
    goal_id: Optional[uuid.UUID] = None
    recurring_id: Optional[uuid.UUID] = None
    transaction_ids: list[uuid.UUID] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
