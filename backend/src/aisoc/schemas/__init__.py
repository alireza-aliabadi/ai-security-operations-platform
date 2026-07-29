"""Pydantic schema package."""

from aisoc.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    MeResponse,
    OIDCCallbackRequest,
    OIDCLoginResponse,
    RefreshRequest,
    TokenResponse,
)
from aisoc.schemas.common import (
    AuditLogRead,
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
)
from aisoc.schemas.connectors import ConnectorCreate, ConnectorListResponse, ConnectorRead, ConnectorUpdate
from aisoc.schemas.investigations import (
    ApprovalCreate,
    ApprovalDecide,
    ApprovalRead,
    InvestigationCreate,
    InvestigationListResponse,
    InvestigationRead,
    InvestigationUpdate,
)
from aisoc.schemas.users import UserCreate, UserListResponse, UserRead, UserUpdate

__all__ = [
    "LoginRequest",
    "LogoutRequest",
    "MeResponse",
    "OIDCCallbackRequest",
    "OIDCLoginResponse",
    "RefreshRequest",
    "TokenResponse",
    "AuditLogRead",
    "ErrorResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationParams",
    "ConnectorCreate",
    "ConnectorListResponse",
    "ConnectorRead",
    "ConnectorUpdate",
    "ApprovalCreate",
    "ApprovalDecide",
    "ApprovalRead",
    "InvestigationCreate",
    "InvestigationListResponse",
    "InvestigationRead",
    "InvestigationUpdate",
    "UserCreate",
    "UserListResponse",
    "UserRead",
    "UserUpdate",
]
