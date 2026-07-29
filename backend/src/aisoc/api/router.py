"""Top-level API router mounting versioned route modules."""

from __future__ import annotations

from fastapi import APIRouter

from aisoc.api.v1 import (
    admin,
    approvals,
    auth,
    chat,
    connectors,
    investigations,
    knowledge,
    reports,
    threat_intel,
    users,
)

api_router = APIRouter()
v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth.router)
v1_router.include_router(users.router)
v1_router.include_router(admin.router)
v1_router.include_router(connectors.router)
v1_router.include_router(investigations.router)
v1_router.include_router(chat.router)
v1_router.include_router(reports.router)
v1_router.include_router(approvals.router)
v1_router.include_router(knowledge.router)
v1_router.include_router(threat_intel.router)

api_router.include_router(v1_router)
