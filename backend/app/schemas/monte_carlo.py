from typing import Literal, Optional
import uuid

from pydantic import BaseModel, Field


class InvestmentPot(BaseModel):
    id: str
    name: str
    starting_balance: float
    account_id: Optional[uuid.UUID] = None
    asset_class: Literal["aggressive", "growth", "balanced", "conservative", "cash", "custom"] = "balanced"
    expected_return: float = 7.5  # Annual expected return in %
    volatility: float = 11.0      # Annual standard deviation in %
    access_age: Optional[int] = None  # None = accessible now
    tax_rate: float = 0.0         # Effective withdrawal tax %
    fee_annual_percent: float = 0.20  # Annual fee % of balance


class ContributionPlan(BaseModel):
    id: str
    name: str
    pot_id: str
    amount_annual: float
    start_age: Optional[int] = None  # None = current age
    end_age: Optional[int] = None    # None = until retirement
    adjust_for_inflation: bool = True


class SpendingPhase(BaseModel):
    id: str
    name: str
    start_age: int
    amount_annual: float


class MonteCarloRequest(BaseModel):
    current_age: int = Field(default=35, ge=18, le=100)
    target_age: int = Field(default=90, ge=30, le=120)
    num_simulations: int = Field(default=1000, ge=100, le=5000)
    inflation_mean: float = Field(default=2.5, ge=0.0, le=20.0)
    inflation_std: float = Field(default=1.5, ge=0.0, le=10.0)
    pots: list[InvestmentPot] = Field(default_factory=list)
    contributions: list[ContributionPlan] = Field(default_factory=list)
    spending_phases: list[SpendingPhase] = Field(default_factory=list)
    withdrawal_strategy: Literal["proportional", "drain_order", "best_performer"] = "proportional"
    min_annual_withdrawal: float = Field(default=0.0, ge=0.0)


class YearlyPercentile(BaseModel):
    age: int
    year: int
    p10: float
    p25: float
    p50: float  # Median
    p75: float
    p90: float


class FailureDistribution(BaseModel):
    age: int
    count: int
    percentage: float


class MonteCarloResult(BaseModel):
    success_rate: float
    median_ending_balance: float
    median_total_withdrawn: float
    chance_of_running_out: float
    typical_failure_age: Optional[int] = None
    percentiles: list[YearlyPercentile]
    failure_histogram: list[FailureDistribution]
    total_simulations: int
    currency: str
