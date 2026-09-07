import pytest

from app.schemas.monte_carlo import (
    ContributionPlan,
    InvestmentPot,
    MonteCarloRequest,
    SpendingPhase,
)
from app.services.monte_carlo_service import (
    build_default_monte_carlo_config,
    run_monte_carlo_simulation,
)


def test_monte_carlo_simulation_basic():
    """Verify simulation executes and produces ordered percentiles and valid metrics."""
    req = MonteCarloRequest(
        current_age=40,
        target_age=70,
        num_simulations=500,
        inflation_mean=2.0,
        inflation_std=1.0,
        pots=[
            InvestmentPot(
                id="pot-1",
                name="Stock Portfolio",
                starting_balance=200000.0,
                asset_class="aggressive",
                expected_return=9.5,
                volatility=15.0,
                fee_annual_percent=0.15,
            )
        ],
        contributions=[
            ContributionPlan(
                id="contrib-1",
                name="Monthly Savings",
                pot_id="pot-1",
                amount_annual=12000.0,
                start_age=40,
                end_age=60,
                adjust_for_inflation=True,
            )
        ],
        spending_phases=[
            SpendingPhase(
                id="phase-1",
                name="Retirement",
                start_age=60,
                amount_annual=40000.0,
            )
        ],
        withdrawal_strategy="proportional",
        min_annual_withdrawal=20000.0,
    )

    result = run_monte_carlo_simulation(req, currency="USD")

    assert 0.0 <= result.success_rate <= 100.0
    assert result.chance_of_running_out == round(100.0 - result.success_rate, 1)
    assert result.total_simulations == 500
    assert len(result.percentiles) == (70 - 40 + 1)

    # Verify percentiles ordering: p10 <= p25 <= p50 <= p75 <= p90
    for p in result.percentiles:
        assert p.p10 <= p.p25 <= p.p50 <= p.p75 <= p.p90

    # Start balance of median at age 40 should be close to starting balance
    assert abs(result.percentiles[0].p50 - 200000.0) < 50000.0


def test_monte_carlo_multi_pot_withdrawal_strategies():
    """Verify drain_order and best_performer withdrawal strategies."""
    pots = [
        InvestmentPot(
            id="cash-pot",
            name="Cash Reserve",
            starting_balance=50000.0,
            asset_class="cash",
            expected_return=3.0,
            volatility=1.0,
        ),
        InvestmentPot(
            id="growth-pot",
            name="Growth Equities",
            starting_balance=150000.0,
            asset_class="growth",
            expected_return=8.5,
            volatility=13.0,
            access_age=50,  # locked until 50
        ),
    ]

    req_drain = MonteCarloRequest(
        current_age=45,
        target_age=65,
        num_simulations=300,
        pots=pots,
        spending_phases=[
            SpendingPhase(
                id="ret-spend",
                name="Spend",
                start_age=45,
                amount_annual=20000.0,
            )
        ],
        withdrawal_strategy="drain_order",
    )

    result_drain = run_monte_carlo_simulation(req_drain, currency="USD")
    assert result_drain.success_rate > 0.0

    req_best = req_drain.model_copy(update={"withdrawal_strategy": "best_performer"})
    result_best = run_monte_carlo_simulation(req_best, currency="USD")
    assert result_best.success_rate > 0.0


@pytest.mark.asyncio
async def test_api_monte_carlo_endpoints(client, auth_headers, session, test_workspace, test_user):
    """Test POST simulation and GET default config endpoints."""
    # 1. Test GET default config
    cfg_res = await client.get("/api/planning/monte-carlo/default-config", headers=auth_headers)
    assert cfg_res.status_code == 200
    cfg_data = cfg_res.json()
    assert "current_age" in cfg_data
    assert "target_age" in cfg_data
    assert "pots" in cfg_data
    assert len(cfg_data["pots"]) > 0

    # 2. Test POST simulation with the returned config
    sim_res = await client.post(
        "/api/planning/monte-carlo",
        headers=auth_headers,
        json=cfg_data,
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert "success_rate" in sim_data
    assert "median_ending_balance" in sim_data
    assert "percentiles" in sim_data
    assert len(sim_data["percentiles"]) > 0
