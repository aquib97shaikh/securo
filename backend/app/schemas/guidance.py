from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    impact: float = Field(..., ge=0, le=100)
    urgency: float = Field(..., ge=0, le=100)
    persistence: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=100)
    relevance: float = Field(..., ge=0, le=100)
    total_score: float = Field(..., ge=0, le=100)


class EvidenceTransaction(BaseModel):
    id: str
    date: str
    description: str
    amount: Decimal
    category_name: Optional[str] = None
    account_name: Optional[str] = None


class EvidenceBudget(BaseModel):
    category_id: str
    category_name: str
    budget_amount: Decimal
    actual_amount: Decimal
    variance: Decimal
    pct_used: float


class EvidenceGoal(BaseModel):
    goal_id: str
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: Optional[str] = None
    on_track: str
    monthly_needed: Decimal


class EvidenceRecurring(BaseModel):
    recurring_id: str
    name: str
    amount: Decimal
    frequency: str
    next_date: Optional[str] = None
    previous_amount: Optional[Decimal] = None
    increase_pct: Optional[float] = None


class EvidenceForecastPoint(BaseModel):
    date: str
    projected_balance: Decimal
    net_change: Decimal
    events: list[str] = Field(default_factory=list)
    has_shortfall: bool = False


class EvidenceData(BaseModel):
    transactions: list[EvidenceTransaction] = Field(default_factory=list)
    budget: Optional[EvidenceBudget] = None
    goal: Optional[EvidenceGoal] = None
    recurring: Optional[EvidenceRecurring] = None
    forecast_points: list[EvidenceForecastPoint] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class RecommendedAction(BaseModel):
    type: str  # cap_budget, reallocate_budget, review_subscription, pause_recurring, delay_spend, buffer_deposit, increase_goal_pace, habit_guardrail
    label: str
    url: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


class GuidanceInsight(BaseModel):
    id: str
    signal_type: str
    family: str  # budget_control, recurring_optimization, cash_flow_safety, goal_recovery, habit_correction
    severity: str  # urgent, action_needed, watch, informational
    score: float
    score_breakdown: ScoreBreakdown
    title: str
    one_line_explanation: str
    impact_amount: Optional[Decimal] = None
    currency: str = "USD"
    what_happened: str
    why_it_matters: str
    how_calculated: str
    next_action: str
    action: RecommendedAction
    evidence: EvidenceData
    created_at: str


class GuidanceSummaryStats(BaseModel):
    total_active: int
    urgent_count: int
    action_needed_count: int
    watch_count: int
    informational_count: int
    total_at_risk_amount: Decimal


class CashFlowForecastStripItem(BaseModel):
    date: str
    day_label: str
    projected_balance: Decimal
    net_change: Decimal
    inflows: Decimal
    outflows: Decimal
    has_shortfall: bool
    events: list[str] = Field(default_factory=list)


class MonthAtRiskItem(BaseModel):
    id: str
    type: str  # category_overspend, upcoming_bill, missed_payment, goal_behind, cash_shortfall
    name: str
    amount: Decimal
    severity: str  # urgent, action_needed, watch
    status_label: str
    url: Optional[str] = None


class SpendingChangeItem(BaseModel):
    category_id: str
    category_name: str
    category_icon: Optional[str] = None
    category_color: Optional[str] = None
    current_amount: Decimal
    baseline_amount: Decimal
    change_pct: float
    direction: str  # increase, decrease


class GuidanceResponse(BaseModel):
    insights: list[GuidanceInsight]
    summary: GuidanceSummaryStats
    cashflow_strip: list[CashFlowForecastStripItem]
    month_at_risk: list[MonthAtRiskItem]
    spending_changes: list[SpendingChangeItem]
    currency: str
    as_of: str


class GuidanceFeedbackCreate(BaseModel):
    status: Optional[str] = None  # active, snoozed, dismissed
    snooze_days: Optional[int] = None  # 7 or 30
    is_helpful: Optional[bool] = None
    action_taken: Optional[str] = None
    feedback_notes: Optional[str] = None


class GuidanceHistoryItem(BaseModel):
    id: str
    insight_id: str
    title: str
    severity: str
    status: str
    snoozed_until: Optional[str] = None
    is_helpful: Optional[bool] = None
    action_taken: Optional[str] = None
    created_at: str
    updated_at: str
