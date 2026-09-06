from datetime import date
from decimal import Decimal
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.workspace_context import WorkspaceContext, current_workspace
from app.schemas.guidance import (
    GuidanceFeedbackCreate,
    GuidanceHistoryItem,
    GuidanceResponse,
)
from app.services.guidance import (
    generate_guidance,
    get_guidance_history,
    record_guidance_feedback,
)

router = APIRouter(prefix="/api/guidance", tags=["guidance"])


from app.models.budget import Budget
from sqlalchemy import select


@router.get("", response_model=GuidanceResponse)
async def get_guidance(
    month: Optional[date] = Query(None),
    context: Optional[str] = Query(None),
    min_score: float = Query(0.0),
    limit: Optional[int] = Query(None),
    safety_buffer: Decimal = Query(Decimal("0.00"), ge=0),
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Retrieve active guidance insights ranked by severity, cashflow forecast strip,

    month-at-risk analysis, and spending changes.
    """
    return await generate_guidance(
        session=session,
        workspace_id=ctx.workspace.id,
        user_id=ctx.user_id,
        target_month=month,
        safety_buffer=safety_buffer,
        context=context,
        min_score=min_score,
        limit=limit,
    )


@router.post("/{insight_id}/feedback", response_model=GuidanceHistoryItem)
async def submit_guidance_feedback(
    insight_id: str,
    payload: GuidanceFeedbackCreate,
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Record dismissal, snooze (7 or 30 days), or helpful/unhelpful rating."""
    record = await record_guidance_feedback(
        session=session,
        workspace_id=ctx.workspace.id,
        user_id=ctx.user_id,
        insight_id=insight_id,
        payload=payload,
    )
    return GuidanceHistoryItem(
        id=str(record.id),
        insight_id=record.insight_id,
        title=record.insight_id.replace("_", " ").title(),
        severity="info",
        status=record.status,
        snoozed_until=record.snoozed_until.isoformat() if record.snoozed_until else None,
        is_helpful=record.is_helpful,
        action_taken=record.action_taken,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat(),
    )


@router.get("/history", response_model=list[GuidanceHistoryItem])
async def get_history(
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Retrieve history of user feedback and acted-on guidance recommendations."""
    return await get_guidance_history(
        session=session,
        workspace_id=ctx.workspace.id,
    )


@router.post("/{insight_id}/action")
async def apply_guidance_action(
    insight_id: str,
    payload: dict[str, Any],
    ctx: WorkspaceContext = Depends(current_workspace),
    session: AsyncSession = Depends(get_async_session),
):
    """Execute in-situ remedy or mark guidance action as executed."""
    action_type = payload.get("action_type") or payload.get("action_id") or "executed"

    budget_action_types = {
        "cap_budget",
        "tune_budget_cap",
        "update_budget",
        "adjust_budget",
        "weekly_guardrail",
        "reallocate_budget",
    }

    # If action_type is generic or not passed, infer from category_id / insight_id
    if action_type == "executed":
        if payload.get("category_id") or "budget" in insight_id or "cap" in insight_id:
            action_type = "cap_budget"

    # 1. Direct 1-click execution for budget remedies
    if action_type in budget_action_types:
        cat_id_str = payload.get("category_id")
        if not cat_id_str and ":" in insight_id:
            # Try to extract category_id from insight_id suffix
            candidate = insight_id.split(":")[-1]
            try:
                uuid.UUID(candidate)
                cat_id_str = candidate
            except ValueError:
                pass

        suggested_amt = payload.get("suggested_amount") or payload.get("amount")
        if cat_id_str:
            try:
                cat_id = uuid.UUID(str(cat_id_str))
                today_month = date.today().replace(day=1)
                b_stmt = select(Budget).where(
                    Budget.workspace_id == ctx.workspace.id,
                    Budget.category_id == cat_id,
                    Budget.month == today_month,
                )
                b_res = await session.execute(b_stmt)
                existing_b = b_res.scalars().first()

                if suggested_amt is not None:
                    amt = Decimal(str(suggested_amt))
                elif existing_b and existing_b.amount:
                    # Provide an automatic 10% safety cushion if amount was not explicitly passed
                    amt = round(existing_b.amount * Decimal("1.10"), 2)
                else:
                    # Look up latest budget for fallback amount
                    prev_stmt = select(Budget).where(
                        Budget.workspace_id == ctx.workspace.id,
                        Budget.category_id == cat_id,
                    ).order_by(Budget.month.desc())
                    prev_res = await session.execute(prev_stmt)
                    prev_b = prev_res.scalars().first()
                    if prev_b and prev_b.amount:
                        amt = round(prev_b.amount * Decimal("1.10"), 2)
                    else:
                        amt = Decimal("250.00")

                if existing_b:
                    existing_b.amount = amt
                else:
                    new_b = Budget(
                        user_id=ctx.user_id,
                        workspace_id=ctx.workspace.id,
                        category_id=cat_id,
                        amount=amt,
                        month=today_month,
                        is_recurring=True,
                    )
                    session.add(new_b)
                await session.commit()
            except Exception:
                pass

    # 2. Record feedback, snooze for 30 days so the insight is immediately resolved
    await record_guidance_feedback(
        session=session,
        workspace_id=ctx.workspace.id,
        user_id=ctx.user_id,
        insight_id=insight_id,
        payload=GuidanceFeedbackCreate(
            status="snoozed",
            snooze_days=30,
            is_helpful=True,
            action_taken=action_type,
        ),
    )
    return {
        "status": "success",
        "insight_id": insight_id,
        "action_taken": action_type,
        "message": "Action applied successfully",
    }

