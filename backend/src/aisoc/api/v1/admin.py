"""Admin endpoints including immutable audit log listing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from aisoc.api.deps import DbSession, require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import AuditLog, User
from aisoc.schemas.common import AuditLogRead, PaginatedResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogRead])
async def list_audit_logs(
    db: DbSession,
    _: User = Depends(require_permissions(Permission.AUDIT_READ)),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    actor_id: str | None = Query(None),
) -> PaginatedResponse[AuditLogRead]:
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
        count_stmt = count_stmt.where(AuditLog.resource_type == resource_type)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
        count_stmt = count_stmt.where(AuditLog.actor_id == actor_id)

    total = await db.scalar(count_stmt) or 0
    result = await db.scalars(
        stmt.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [AuditLogRead.model_validate(row) for row in result.all()]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
