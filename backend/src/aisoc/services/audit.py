"""Audit log service helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from aisoc.db.models import AuditLog


async def write_audit(
    session: AsyncSession,
    *,
    action: str,
    resource_type: str,
    actor_id: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip=ip,
    )
    session.add(entry)
    await session.flush()
    return entry
