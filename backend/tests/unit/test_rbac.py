"""Unit tests for RBAC role → permission mapping."""

from __future__ import annotations

from aisoc.core.rbac import Permission, Role, has_permission, permissions_for_roles


def test_admin_has_all_permissions() -> None:
    perms = permissions_for_roles([Role.ADMIN])
    assert perms == set(Permission)
    assert has_permission(["admin"], Permission.USERS_ADMIN)


def test_analyst_permissions() -> None:
    perms = permissions_for_roles(["analyst"])
    assert Permission.INVESTIGATIONS_WRITE in perms
    assert Permission.CHAT_USE in perms
    assert Permission.USERS_ADMIN not in perms
    assert Permission.AUDIT_READ not in perms
    assert has_permission(["analyst"], "investigations:read")


def test_viewer_is_read_mostly() -> None:
    perms = permissions_for_roles([Role.VIEWER])
    assert Permission.INVESTIGATIONS_READ in perms
    assert Permission.INVESTIGATIONS_WRITE not in perms
    assert Permission.APPROVALS_WRITE not in perms
    assert Permission.CHAT_USE in perms


def test_auditor_can_read_audit() -> None:
    perms = permissions_for_roles([Role.AUDITOR])
    assert Permission.AUDIT_READ in perms
    assert Permission.INVESTIGATIONS_WRITE not in perms
    assert has_permission(["auditor"], Permission.AUDIT_READ)


def test_combined_roles_union() -> None:
    perms = permissions_for_roles(["viewer", "auditor"])
    assert Permission.AUDIT_READ in perms
    assert Permission.CHAT_USE in perms
