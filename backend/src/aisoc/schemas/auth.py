"""Authentication request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from aisoc.schemas.common import EmailAddress
from aisoc.schemas.users import UserRead


class LoginRequest(BaseModel):
    email: EmailAddress
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class MeResponse(UserRead):
    permissions: list[str]


class OIDCLoginResponse(BaseModel):
    authorization_url: str
    state: str


class OIDCCallbackRequest(BaseModel):
    code: str
    state: str | None = None


class OIDCTokenExchange(BaseModel):
    """Simplified mock OIDC token payload used by the mock issuer flow."""

    access_token: str | None = None
    id_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    sub: str | None = None
    email: EmailAddress | None = None
    name: str | None = None
    roles: list[str] = Field(default_factory=list)
