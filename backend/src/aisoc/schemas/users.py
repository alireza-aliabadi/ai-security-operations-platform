"""User schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from aisoc.schemas.common import EmailAddress, ORMModel


class UserRead(ORMModel):
    id: str
    email: EmailAddress
    full_name: str
    is_active: bool
    roles: list[str]
    oidc_sub: str | None = None
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailAddress
    password: str = Field(min_length=8)
    full_name: str = ""
    roles: list[str] = Field(default_factory=lambda: ["analyst"])
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    roles: list[str] | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8)


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int
