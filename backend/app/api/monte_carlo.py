"""Monte Carlo Analysis API endpoints for long-term retirement and wealth survival planning."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_async_session
from app.core.workspace_context import WorkspaceContext, current_workspace
from app.models.user import User
from app.schemas.monte_carlo import MonteCarloRequest, MonteCarloResult
from app.services.monte_carlo_service import (
    build_default_monte_carlo_config,
    run_monte_carlo_simulation,
)

router = APIRouter(prefix="/api/planning/monte-carlo", tags=["planning"])


@router.post("", response_model=MonteCarloResult)
async def simulate_monte_carlo(
    req: MonteCarloRequest,
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
) -> MonteCarloResult:
    """Run Monte Carlo retirement & wealth trajectory simulation."""
    user = await session.get(User, ctx.user_id)
    currency = user.primary_currency if user else get_settings().default_currency

    return run_monte_carlo_simulation(req, currency=currency)


@router.get("/default-config", response_model=MonteCarloRequest)
async def get_monte_carlo_default_config(
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
) -> MonteCarloRequest:
    """Get sensible default Monte Carlo simulation parameters seeded from active accounts."""
    return await build_default_monte_carlo_config(
        session=session,
        workspace_id=ctx.workspace.id,
        user_id=ctx.user_id,
    )
