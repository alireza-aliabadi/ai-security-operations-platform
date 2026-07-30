"""Authentication endpoints: password login, refresh, logout, me, and mock OIDC."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aisoc.api.deps import CurrentUser, DbSession, get_settings_dep
from aisoc.core.config import Settings
from aisoc.core.rbac import Role, permissions_for_roles
from aisoc.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from aisoc.db.models import RefreshToken, User
from aisoc.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    OIDCCallbackRequest,
    OIDCLoginResponse,
    RefreshRequest,
    TokenResponse,
)
from aisoc.schemas.common import MessageResponse
from aisoc.services.audit import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _token_response(
    user: User,
    access: str,
    refresh: str,
    settings: Settings,
) -> TokenResponse:
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def _issue_tokens(
    session: AsyncSession,
    user: User,
    settings: Settings,
) -> tuple[str, str]:
    roles = [str(r) for r in (user.roles or [])]
    access = create_access_token(user.id, roles, settings=settings)
    refresh = create_refresh_token(user.id, settings=settings)
    payload = decode_token(refresh, settings=settings)
    jti = str(payload["jti"])
    expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=UTC)
    session.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
            revoked=False,
        )
    )
    await session.flush()
    return access, refresh


def _sign_state(state: str, secret: str) -> str:
    sig = hmac.new(secret.encode(), state.encode(), hashlib.sha256).hexdigest()
    return f"{state}.{sig}"


def _verify_state(signed: str, secret: str) -> str:
    if "." not in signed:
        raise ValueError("Invalid state")
    state, sig = signed.rsplit(".", 1)
    expected = hmac.new(secret.encode(), state.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Invalid state signature")
    return state


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: DbSession,
    settings: Settings = Depends(get_settings_dep),
) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access, refresh = await _issue_tokens(db, user, settings)
    await write_audit(
        db,
        actor_id=user.id,
        action="auth.login",
        resource_type="user",
        resource_id=user.id,
        details={"method": "password"},
        ip=_client_ip(request),
    )
    return _token_response(user, access, refresh, settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshRequest,
    request: Request,
    db: DbSession,
    settings: Settings = Depends(get_settings_dep),
) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")
    if not jti or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    stored = await db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if stored is None or stored.revoked or stored.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or unknown"
        )
    if stored.expires_at < datetime.now(UTC):
        stored.revoked = True
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive"
        )

    stored.revoked = True
    access, refresh = await _issue_tokens(db, user, settings)
    await write_audit(
        db,
        actor_id=user.id,
        action="auth.refresh",
        resource_type="user",
        resource_id=user.id,
        details={},
        ip=_client_ip(request),
    )
    return _token_response(user, access, refresh, settings)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: LogoutRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    settings: Settings = Depends(get_settings_dep),
) -> MessageResponse:
    if body.refresh_token:
        try:
            payload = decode_token(body.refresh_token, settings=settings)
            jti = payload.get("jti")
            if jti:
                stored = await db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
                if stored is not None and stored.user_id == user.id:
                    stored.revoked = True
        except ValueError:
            pass

    await write_audit(
        db,
        actor_id=user.id,
        action="auth.logout",
        resource_type="user",
        resource_id=user.id,
        details={},
        ip=_client_ip(request),
    )
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser) -> MeResponse:
    roles = [str(r) for r in (user.roles or [])]
    perms = sorted(p.value for p in permissions_for_roles(roles))
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=roles,
        oidc_sub=user.oidc_sub,
        created_at=user.created_at,
        updated_at=user.updated_at,
        permissions=perms,
    )


@router.get("/oidc/login", response_model=OIDCLoginResponse)
async def oidc_login(
    settings: Settings = Depends(get_settings_dep),
) -> OIDCLoginResponse:
    if not settings.oidc_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OIDC disabled")

    nonce = secrets.token_urlsafe(16)
    state = _sign_state(nonce, settings.secret_key)
    params = {
        "client_id": settings.oidc_client_id,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": settings.oidc_redirect_uri,
        "state": state,
    }
    authorization_url = f"{settings.oidc_issuer.rstrip('/')}/protocol/openid-connect/auth?{urlencode(params)}"
    return OIDCLoginResponse(authorization_url=authorization_url, state=state)


@router.get("/oidc/callback", response_model=TokenResponse)
async def oidc_callback_get(
    request: Request,
    db: DbSession,
    code: str = Query(...),
    state: str | None = Query(None),
    settings: Settings = Depends(get_settings_dep),
) -> TokenResponse:
    return await _oidc_exchange(db, request, code=code, state=state, settings=settings)


@router.post("/oidc/callback", response_model=TokenResponse)
async def oidc_callback_post(
    body: OIDCCallbackRequest,
    request: Request,
    db: DbSession,
    settings: Settings = Depends(get_settings_dep),
) -> TokenResponse:
    return await _oidc_exchange(
        db, request, code=body.code, state=body.state, settings=settings
    )


async def _oidc_exchange(
    db: AsyncSession,
    request: Request,
    *,
    code: str,
    state: str | None,
    settings: Settings,
) -> TokenResponse:
    if not settings.oidc_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OIDC disabled")

    if state:
        try:
            _verify_state(state, settings.secret_key)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OIDC state"
            ) from exc

    claims = await _exchange_oidc_code(code, settings)
    email = str(claims.get("email") or "").lower()
    sub = str(claims.get("sub") or "")
    if not email or not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC token missing email or sub",
        )

    roles_raw = claims.get("roles") or claims.get("realm_access", {}).get("roles") or []
    if isinstance(roles_raw, dict):
        roles_raw = roles_raw.get("roles", [])
    roles = [str(r) for r in roles_raw if str(r) in {m.value for m in Role}]
    if not roles:
        roles = [Role.ANALYST.value]

    user = await db.scalar(select(User).where((User.oidc_sub == sub) | (User.email == email)))
    if user is None:
        user = User(
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            full_name=str(claims.get("name") or claims.get("preferred_username") or email),
            is_active=True,
            roles=roles,
            oidc_sub=sub,
        )
        db.add(user)
        await db.flush()
    else:
        user.oidc_sub = sub
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access, refresh = await _issue_tokens(db, user, settings)
    await write_audit(
        db,
        actor_id=user.id,
        action="auth.oidc_login",
        resource_type="user",
        resource_id=user.id,
        details={"sub": sub},
        ip=_client_ip(request),
    )
    return _token_response(user, access, refresh, settings)


async def _exchange_oidc_code(code: str, settings: Settings) -> dict[str, Any]:
    """Exchange authorization code with the OIDC issuer, or accept mock codes.

    Mock issuer support:
    - code starting with ``mock:`` is treated as ``mock:<sub>:<email>``
    - otherwise performs a standard token endpoint exchange (Authlib-compatible).
    """
    if code.startswith("mock:"):
        parts = code.split(":", 2)
        if len(parts) != 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid mock OIDC code; expected mock:<sub>:<email>",
            )
        _, sub, email = parts
        return {
            "sub": sub or str(uuid4()),
            "email": email,
            "name": email.split("@")[0],
            "roles": [Role.ANALYST.value],
        }

    token_url = f"{settings.oidc_issuer.rstrip('/')}/protocol/openid-connect/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.oidc_redirect_uri,
        "client_id": settings.oidc_client_id,
        "client_secret": settings.oidc_client_secret,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(token_url, data=data)
    except httpx.HTTPError as exc:
        # Development fallback: decode opaque mock JWT-like codes signed with secret_key
        claims = _try_decode_dev_code(code, settings)
        if claims is not None:
            return claims
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OIDC token exchange failed: {exc}",
        ) from exc

    if response.status_code >= 400:
        claims = _try_decode_dev_code(code, settings)
        if claims is not None:
            return claims
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OIDC token exchange rejected",
        )

    token_payload = response.json()
    id_token = token_payload.get("id_token")
    if id_token:
        try:
            # Signature verification against issuer JWKS is deferred; decode for claims.
            # In production, configure Authlib/OIDC with JWKS verification.
            claims = jwt.get_unverified_claims(id_token)
            if "email" not in claims and token_payload.get("email"):
                claims["email"] = token_payload["email"]
            return claims
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OIDC id_token"
            ) from exc

    if token_payload.get("sub") and token_payload.get("email"):
        return token_payload

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OIDC response missing identity claims",
    )


def _try_decode_dev_code(code: str, settings: Settings) -> dict[str, Any] | None:
    """Allow HS256-signed JWT authorization codes for local mock issuers."""
    try:
        return jwt.decode(code, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
