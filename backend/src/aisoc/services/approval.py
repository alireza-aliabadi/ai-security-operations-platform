"""Human-in-the-loop approval service."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisoc.db.models import Approval, ApprovalStatus, Investigation, InvestigationStatus
from aisoc.services.audit import write_audit


async def create_approval(
    session: AsyncSession,
    *,
    investigation_id: str,
    action: str,
    requested_by: str | None,
    reason: str | None = None,
    ip: str | None = None,
) -> Approval:
    investigation = await session.scalar(
        select(Investigation).where(Investigation.id == investigation_id)
    )
    if investigation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    approval = Approval(
        investigation_id=investigation_id,
        action=action,
        status=ApprovalStatus.PENDING.value,
        requested_by=requested_by,
        reason=reason,
    )
    session.add(approval)
    investigation.status = InvestigationStatus.AWAITING_APPROVAL.value
    await session.flush()

    await write_audit(
        session,
        actor_id=requested_by,
        action="approval.requested",
        resource_type="approval",
        resource_id=approval.id,
        details={"investigation_id": investigation_id, "action": action, "reason": reason},
        ip=ip,
    )
    return approval


async def decide_approval(
    session: AsyncSession,
    *,
    approval_id: str,
    decided_by: str,
    decision: ApprovalStatus | str,
    reason: str | None = None,
    ip: str | None = None,
) -> Approval:
    status_value = ApprovalStatus(decision) if isinstance(decision, str) else decision
    if status_value not in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be approved or rejected",
        )

    approval = await session.scalar(select(Approval).where(Approval.id == approval_id))
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    if approval.status != ApprovalStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approval already decided",
        )

    approval.status = status_value.value
    approval.decided_by = decided_by
    approval.decided_at = datetime.now(UTC)
    if reason is not None:
        approval.reason = reason

    investigation = await session.scalar(
        select(Investigation).where(Investigation.id == approval.investigation_id)
    )
    if investigation is not None:
        if status_value == ApprovalStatus.APPROVED:
            investigation.status = InvestigationStatus.RUNNING.value
        else:
            investigation.status = InvestigationStatus.FAILED.value

    await session.flush()
    await write_audit(
        session,
        actor_id=decided_by,
        action=f"approval.{status_value.value}",
        resource_type="approval",
        resource_id=approval.id,
        details={
            "investigation_id": approval.investigation_id,
            "action": approval.action,
            "reason": approval.reason,
        },
        ip=ip,
    )
    return approval
