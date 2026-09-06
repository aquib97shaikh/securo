from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.workspace_context import WorkspaceContext, current_workspace
from app.schemas.budget_insights import BudgetInsight
from app.services.budget_insights_service import generate_insights

router = APIRouter(prefix="/api/budgets/insights", tags=["budgets"])


@router.get("", response_model=list[BudgetInsight])
async def get_budget_insights(
    month: Optional[date] = Query(None),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    return await generate_insights(session, ctx.workspace.id, ctx.user_id, month)
