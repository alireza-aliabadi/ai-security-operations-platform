"""RBAC roles and permission helpers."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class Permission(StrEnum):
    INVESTIGATIONS_READ = "investigations:read"
    INVESTIGATIONS_WRITE = "investigations:write"
    CONNECTORS_READ = "connectors:read"
    CONNECTORS_WRITE = "connectors:write"
    REPORTS_READ = "reports:read"
    REPORTS_EXPORT = "reports:export"
    APPROVALS_READ = "approvals:read"
    APPROVALS_WRITE = "approvals:write"
    USERS_ADMIN = "users:admin"
    AUDIT_READ = "audit:read"
    CHAT_USE = "chat:use"
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),
    Role.ANALYST: {
        Permission.INVESTIGATIONS_READ,
        Permission.INVESTIGATIONS_WRITE,
        Permission.CONNECTORS_READ,
        Permission.REPORTS_READ,
        Permission.REPORTS_EXPORT,
        Permission.APPROVALS_READ,
        Permission.APPROVALS_WRITE,
        Permission.CHAT_USE,
        Permission.KNOWLEDGE_READ,
    },
    Role.VIEWER: {
        Permission.INVESTIGATIONS_READ,
        Permission.CONNECTORS_READ,
        Permission.REPORTS_READ,
        Permission.CHAT_USE,
        Permission.KNOWLEDGE_READ,
    },
    Role.AUDITOR: {
        Permission.INVESTIGATIONS_READ,
        Permission.CONNECTORS_READ,
        Permission.REPORTS_READ,
        Permission.APPROVALS_READ,
        Permission.AUDIT_READ,
        Permission.KNOWLEDGE_READ,
    },
}


def permissions_for_roles(roles: list[str] | list[Role]) -> set[Permission]:
    perms: set[Permission] = set()
    for role in roles:
        r = Role(role) if not isinstance(role, Role) else role
        perms |= ROLE_PERMISSIONS.get(r, set())
    return perms


def has_permission(roles: list[str], permission: Permission | str) -> bool:
    perm = Permission(permission) if isinstance(permission, str) else permission
    return perm in permissions_for_roles(roles)
