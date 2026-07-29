"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisoc.core.config import Settings, get_settings
from aisoc.core.rbac import Permission, Role, has_permission
from aisoc.core.security import decode_token
from aisoc.db.models import User
from aisoc.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(lambda: get_settings())]


def get_settings_dep() -> Settings:
    return get_settings()


def _mcp_service_user() -> Any:
    """Synthetic principal for MCP_API_TOKEN service-to-service auth."""
    return SimpleNamespace(
        id="mcp-service",
        email="mcp@aisoc.local",
        full_name="MCP Service",
        is_active=True,
        roles=[Role.ADMIN.value],
    )


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings_dep)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Allow MCP server to authenticate with the shared service token
    if credentials.credentials == settings.mcp_api_token:
        return _mcp_service_user()  # type: ignore[return-value]

    try:
        payload = decode_token(credentials.credentials, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permissions(*perms: Permission | str) -> Callable[..., User]:
    required = [
        Permission(p) if isinstance(p, str) else p for p in perms
    ]

    async def _dependency(user: CurrentUser) -> User:
        roles = [str(r) for r in (user.roles or [])]
        missing = [p for p in required if not has_permission(roles, p)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(p.value for p in missing)}",
            )
        return user

    return _dependency
