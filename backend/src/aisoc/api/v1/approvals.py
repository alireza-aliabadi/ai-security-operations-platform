"""Human-in-the-loop approval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from aisoc.api.deps import DbSession, require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import Approval, User
from aisoc.schemas.investigations import ApprovalCreate, ApprovalDecide, ApprovalRead
from aisoc.services.approval import create_approval, decide_approval

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRead])
async def list_approvals(
    db: DbSession,
    _: User = Depends(require_permissions(Permission.APPROVALS_READ)),
    status_filter: str | None = Query(None, alias="status"),
    investigation_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[ApprovalRead]:
    stmt = select(Approval).order_by(Approval.created_at.desc())
    if status_filter:
        stmt = stmt.where(Approval.status == status_filter)
    if investigation_id:
        stmt = stmt.where(Approval.investigation_id == investigation_id)
    rows = list((await db.scalars(stmt)).all())
    start = (page - 1) * page_size
    return [ApprovalRead.model_validate(r) for r in rows[start : start + page_size]]


@router.post("", response_model=ApprovalRead, status_code=status.HTTP_201_CREATED)
async def create_approval_endpoint(
    body: ApprovalCreate,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.APPROVALS_WRITE)),
) -> ApprovalRead:
    approval = await create_approval(
        db,
        investigation_id=body.investigation_id,
        action=body.action,
        requested_by=user.id,
        reason=body.reason,
    )
    return ApprovalRead.model_validate(approval)


@router.get("/{approval_id}", response_model=ApprovalRead)
async def get_approval(
    approval_id: str,
    db: DbSession,
    _: User = Depends(require_permissions(Permission.APPROVALS_READ)),
) -> ApprovalRead:
    approval = await db.scalar(select(Approval).where(Approval.id == approval_id))
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return ApprovalRead.model_validate(approval)


@router.post("/{approval_id}/decide", response_model=ApprovalRead)
async def decide_approval_endpoint(
    approval_id: str,
    body: ApprovalDecide,
    db: DbSession,
    user: User = Depends(require_permissions(Permission.APPROVALS_WRITE)),
) -> ApprovalRead:
    approval = await decide_approval(
        db,
        approval_id=approval_id,
        decided_by=user.id,
        decision=body.status,
        reason=body.reason,
    )
    return ApprovalRead.model_validate(approval)
