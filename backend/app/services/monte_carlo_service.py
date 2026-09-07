"""Monte Carlo Retirement & Wealth Simulation Service.

Implements multi-pot portfolio simulation, stochastic inflation, contribution accumulation,
phased withdrawals, and failure probability distribution analysis.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
import uuid

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User
from app.schemas.monte_carlo import (
    ContributionPlan,
    FailureDistribution,
    InvestmentPot,
    MonteCarloRequest,
    MonteCarloResult,
    SpendingPhase,
    YearlyPercentile,
)
from app.services.account_service import get_accounts
from app.services.fx_rate_service import convert


# Preset market parameters (Stocks / Bonds / Cash return and volatility)
PORTFOLIO_PRESETS = {
    "aggressive": {"expected_return": 10.0, "volatility": 16.0},
    "growth": {"expected_return": 8.8, "volatility": 13.5},
    "balanced": {"expected_return": 7.5, "volatility": 11.0},
    "conservative": {"expected_return": 6.0, "volatility": 8.0},
    "cash": {"expected_return": 3.5, "volatility": 2.0},
}


def run_monte_carlo_simulation(
    req: MonteCarloRequest,
    currency: str = "USD",
) -> MonteCarloResult:
    """Execute vectorized Monte Carlo retirement & wealth trajectory simulation."""

    current_age = req.current_age
    target_age = req.target_age
    num_sims = req.num_simulations
    num_years = max(1, target_age - current_age + 1)

    pots = list(req.pots)
    if not pots:
        # Fallback default pot if none provided
        pots = [
            InvestmentPot(
                id="default-pot",
                name="Primary Portfolio",
                starting_balance=100000.0,
                asset_class="balanced",
                expected_return=7.5,
                volatility=11.0,
            )
        ]

    num_pots = len(pots)
    # Shape: (num_simulations, num_pots)
    pot_balances = np.zeros((num_sims, num_pots), dtype=np.float64)
    for p_idx, pot in enumerate(pots):
        pot_balances[:, p_idx] = max(0.0, float(pot.starting_balance))

    # Array to track total portfolio balance per simulation across each year
    portfolio_history = np.zeros((num_sims, num_years), dtype=np.float64)
    # Array to track cumulative withdrawals per simulation
    total_withdrawn_per_sim = np.zeros(num_sims, dtype=np.float64)
    # Track age when each simulation ran out of money (0 if survived)
    failure_ages = np.zeros(num_sims, dtype=np.int32)

    # Cumulative inflation multipliers per simulation
    cum_inflation = np.ones(num_sims, dtype=np.float64)

    # Pre-calculate spending schedule by age
    spending_by_age: dict[int, float] = {}
    sorted_phases = sorted(req.spending_phases, key=lambda x: x.start_age)
    for yr_idx in range(num_years):
        age = current_age + yr_idx
        # Find the active spending phase for this age
        active_phase_amt = 0.0
        for ph in sorted_phases:
            if ph.start_age <= age:
                active_phase_amt = float(ph.amount_annual)
        spending_by_age[age] = active_phase_amt

    # Yearly Simulation Loop
    for t in range(num_years):
        age = current_age + t

        # 1. Update inflation for this year
        inf_mean = req.inflation_mean / 100.0
        inf_std = max(0.001, req.inflation_std / 100.0)
        yearly_inf = np.random.normal(inf_mean, inf_std, num_sims)
        yearly_inf = np.clip(yearly_inf, -0.10, 0.40)  # reasonable boundary
        cum_inflation *= (1.0 + yearly_inf)

        # 2. Add Contributions (start of year)
        for contrib in req.contributions:
            start = contrib.start_age if contrib.start_age is not None else current_age
            end = contrib.end_age if contrib.end_age is not None else target_age
            if start <= age <= end:
                c_amt = float(contrib.amount_annual)
                if contrib.adjust_for_inflation:
                    c_amt_arr = c_amt * cum_inflation
                else:
                    c_amt_arr = np.full(num_sims, c_amt)

                # Locate target pot index
                for p_idx, pot in enumerate(pots):
                    if pot.id == contrib.pot_id:
                        # Only add to simulations that have not completely failed
                        alive_mask = failure_ages == 0
                        pot_balances[alive_mask, p_idx] += c_amt_arr[alive_mask]
                        break

        # 3. Investment Returns & Fees
        returns_this_year = np.zeros((num_sims, num_pots), dtype=np.float64)
        for p_idx, pot in enumerate(pots):
            mean_ret = pot.expected_return / 100.0
            vol = max(0.001, pot.volatility / 100.0)
            ret_draw = np.random.normal(mean_ret, vol, num_sims)
            returns_this_year[:, p_idx] = ret_draw

            fee_pct = max(0.0, pot.fee_annual_percent / 100.0)
            net_factor = 1.0 + ret_draw - fee_pct

            alive_mask = failure_ages == 0
            pot_balances[alive_mask, p_idx] *= np.maximum(0.0, net_factor[alive_mask])

        # 4. Withdrawals / Spending (end of year)
        base_spend = spending_by_age.get(age, 0.0)
        target_withdrawal = base_spend * cum_inflation
        min_withdrawal = req.min_annual_withdrawal * cum_inflation
        needed_withdrawal = np.maximum(target_withdrawal, min_withdrawal)

        alive_mask = failure_ages == 0

        # Accessible pots mask for this age
        accessible_pots = [
            p_idx for p_idx, pot in enumerate(pots)
            if pot.access_age is None or pot.access_age <= age
        ]

        if accessible_pots and np.any(needed_withdrawal[alive_mask] > 0):
            if req.withdrawal_strategy == "proportional":
                # Proportional to accessible pot balances
                acc_total = np.sum(pot_balances[:, accessible_pots], axis=1)
                for p_idx in accessible_pots:
                    weight = np.where(acc_total > 0, pot_balances[:, p_idx] / np.maximum(acc_total, 1e-9), 0.0)
                    desired = needed_withdrawal * weight
                    tax_mult = 1.0 / max(0.01, (1.0 - pots[p_idx].tax_rate / 100.0))
                    gross_deduct = desired * tax_mult
                    actual_deduct = np.minimum(pot_balances[:, p_idx], gross_deduct)
                    pot_balances[:, p_idx] -= actual_deduct
                    total_withdrawn_per_sim += actual_deduct / tax_mult

            elif req.withdrawal_strategy == "drain_order":
                # Drain accessible pots in listed order
                rem_need = needed_withdrawal.copy()
                for p_idx in accessible_pots:
                    tax_mult = 1.0 / max(0.01, (1.0 - pots[p_idx].tax_rate / 100.0))
                    gross_need = rem_need * tax_mult
                    actual_deduct = np.minimum(pot_balances[:, p_idx], gross_need)
                    pot_balances[:, p_idx] -= actual_deduct
                    net_got = actual_deduct / tax_mult
                    total_withdrawn_per_sim += net_got
                    rem_need = np.maximum(0.0, rem_need - net_got)

            elif req.withdrawal_strategy == "best_performer":
                # Withdraw from best performing accessible pot first
                rem_need = needed_withdrawal.copy()
                for s in range(num_sims):
                    if not alive_mask[s] or rem_need[s] <= 0:
                        continue
                    # Sort accessible pots by this year's return descending
                    sorted_acc = sorted(accessible_pots, key=lambda idx: returns_this_year[s, idx], reverse=True)
                    for p_idx in sorted_acc:
                        tax_mult = 1.0 / max(0.01, (1.0 - pots[p_idx].tax_rate / 100.0))
                        gross_need = rem_need[s] * tax_mult
                        actual_deduct = min(pot_balances[s, p_idx], gross_need)
                        pot_balances[s, p_idx] -= actual_deduct
                        net_got = actual_deduct / tax_mult
                        total_withdrawn_per_sim[s] += net_got
                        rem_need[s] -= net_got
                        if rem_need[s] <= 0:
                            break

        # Record total portfolio balance across all pots
        tot = np.sum(pot_balances, axis=1)
        portfolio_history[:, t] = tot

        # Check for failure (balance reaches zero)
        just_failed = (alive_mask) & (tot <= 1.0)
        failure_ages[just_failed] = age
        pot_balances[just_failed, :] = 0.0

    # Calculate statistics & metrics
    survived_mask = failure_ages == 0
    success_rate = round(float(np.sum(survived_mask)) / float(num_sims) * 100.0, 1)
    chance_of_running_out = round(100.0 - success_rate, 1)

    median_ending_balance = round(float(np.median(portfolio_history[:, -1])), 2)
    median_total_withdrawn = round(float(np.median(total_withdrawn_per_sim)), 2)

    typical_failure_age = None
    failed_ages_list = failure_ages[failure_ages > 0]
    if len(failed_ages_list) > 0:
        typical_failure_age = int(np.median(failed_ages_list))

    # Calculate percentiles across all years
    percentiles: list[YearlyPercentile] = []
    for t in range(num_years):
        yr_balances = portfolio_history[:, t]
        percentiles.append(
            YearlyPercentile(
                age=current_age + t,
                year=t,
                p10=round(float(np.percentile(yr_balances, 10)), 2),
                p25=round(float(np.percentile(yr_balances, 25)), 2),
                p50=round(float(np.percentile(yr_balances, 50)), 2),
                p75=round(float(np.percentile(yr_balances, 75)), 2),
                p90=round(float(np.percentile(yr_balances, 90)), 2),
            )
        )

    # Calculate failure age histogram
    failure_histogram: list[FailureDistribution] = []
    if len(failed_ages_list) > 0:
        unique_ages, counts = np.unique(failed_ages_list, return_counts=True)
        for u_age, count in zip(unique_ages, counts):
            failure_histogram.append(
                FailureDistribution(
                    age=int(u_age),
                    count=int(count),
                    percentage=round(float(count) / float(num_sims) * 100.0, 2),
                )
            )

    return MonteCarloResult(
        success_rate=success_rate,
        median_ending_balance=median_ending_balance,
        median_total_withdrawn=median_total_withdrawn,
        chance_of_running_out=chance_of_running_out,
        typical_failure_age=typical_failure_age,
        percentiles=percentiles,
        failure_histogram=failure_histogram,
        total_simulations=num_sims,
        currency=currency,
    )


async def build_default_monte_carlo_config(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> MonteCarloRequest:
    """Auto-generate sensible default Monte Carlo inputs from user's active accounts."""

    user = await session.get(User, user_id)
    primary_currency = user.primary_currency if user else get_settings().default_currency
    all_accounts = await get_accounts(session, workspace_id, include_closed=False)

    pots: list[InvestmentPot] = []
    total_liquid = 0.0

    for acc in all_accounts:
        if acc.get("is_closed"):
            continue
        acc_id = acc.get("id")
        name = acc.get("name", "Account")
        acc_type = acc.get("type", "checking")
        raw_bal = Decimal(str(acc.get("current_balance") or 0))

        if raw_bal <= 0 and acc_type == "credit_card":
            continue

        cur = acc.get("currency", primary_currency)
        if cur != primary_currency:
            bal_conv, _ = await convert(session, raw_bal, cur, primary_currency)
            bal_float = float(round(bal_conv, 2))
        else:
            bal_float = float(round(raw_bal, 2))

        if bal_float > 0:
            total_liquid += bal_float
            preset = "cash" if acc_type in ("checking", "cash", "wallet") else "balanced"
            preset_vals = PORTFOLIO_PRESETS[preset]

            pots.append(
                InvestmentPot(
                    id=str(acc_id),
                    name=name,
                    starting_balance=bal_float,
                    account_id=acc_id if isinstance(acc_id, uuid.UUID) else uuid.UUID(str(acc_id)),
                    asset_class=preset,
                    expected_return=preset_vals["expected_return"],
                    volatility=preset_vals["volatility"],
                    fee_annual_percent=0.15,
                )
            )

    # Fallback if user has no accounts with positive balances
    if not pots:
        pots = [
            InvestmentPot(
                id=str(uuid.uuid4()),
                name="Retirement Portfolio",
                starting_balance=50000.0,
                asset_class="balanced",
                expected_return=7.5,
                volatility=11.0,
                fee_annual_percent=0.20,
            )
        ]
        total_liquid = 50000.0

    # Default spending: standard retirement benchmark based on 4% rule or reasonable baseline
    estimated_annual_spending = max(24000.0, round(total_liquid * 0.04, 0))

    return MonteCarloRequest(
        current_age=35,
        target_age=85,
        num_simulations=1000,
        inflation_mean=2.5,
        inflation_std=1.5,
        pots=pots,
        contributions=[
            ContributionPlan(
                id=str(uuid.uuid4()),
                name="Annual Savings",
                pot_id=pots[0].id,
                amount_annual=round(estimated_annual_spending * 0.3, 0),
                start_age=35,
                end_age=65,
                adjust_for_inflation=True,
            )
        ],
        spending_phases=[
            SpendingPhase(
                id=str(uuid.uuid4()),
                name="Retirement Living",
                start_age=65,
                amount_annual=estimated_annual_spending,
            )
        ],
        withdrawal_strategy="proportional",
        min_annual_withdrawal=12000.0,
    )
