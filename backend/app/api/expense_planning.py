import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.workspace_context import WorkspaceContext, current_workspace
from app.schemas.expense_planning import ExpensePlan
from app.services.expense_planning_service import get_expense_plan

router = APIRouter(prefix="/api/planning", tags=["planning"])


@router.get("/expenses", response_model=ExpensePlan)
async def get_expenses_plan(
    months: int = Query(6, ge=1, le=24),
    account_id: Optional[uuid.UUID] = Query(None),
    forecast_mode: str = Query("all", pattern="^(all|recurring_only|budget_only)$"),
    safety_buffer: Decimal = Query(Decimal("0.00"), ge=0),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    return await get_expense_plan(
        session,
        ctx.workspace.id,
        ctx.user_id,
        months=months,
        account_id=account_id,
        forecast_mode=forecast_mode,
        safety_buffer=safety_buffer,
    )
