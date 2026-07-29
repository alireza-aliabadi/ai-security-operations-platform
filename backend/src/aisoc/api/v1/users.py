"""Admin user management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from aisoc.api.deps import DbSession, require_permissions
from aisoc.core.rbac import Permission
from aisoc.db.models import User
from aisoc.schemas.users import UserListResponse, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    _: User = Depends(require_permissions(Permission.USERS_ADMIN)),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> UserListResponse:
    total = await db.scalar(select(func.count()).select_from(User)) or 0
    result = await db.scalars(
        select(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = list(result.all())
    return UserListResponse(
        items=[UserRead.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str,
    db: DbSession,
    _: User = Depends(require_permissions(Permission.USERS_ADMIN)),
) -> UserRead:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead.model_validate(user)
