"""Unit tests for password hashing and JWT helpers."""

from __future__ import annotations

from aisoc.core.config import Settings
from aisoc.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def _settings() -> Settings:
    return Settings(
        app_env="test",
        secret_key="test-secret-key-at-least-32-characters-long!!",
        encryption_key="0123456789abcdef0123456789abcdef",
        llm_primary_api_key="",
    )


def test_hash_and_verify_password() -> None:
    hashed = hash_password("ChangeMeAnalyst123!")
    assert hashed != "ChangeMeAnalyst123!"
    assert verify_password("ChangeMeAnalyst123!", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_access_roundtrip() -> None:
    settings = _settings()
    token = create_access_token("user-123", ["analyst", "viewer"], settings=settings)
    payload = decode_token(token, settings=settings)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert payload["roles"] == ["analyst", "viewer"]
    assert "jti" in payload
    assert "exp" in payload


def test_jwt_refresh_roundtrip() -> None:
    settings = _settings()
    token = create_refresh_token("user-456", settings=settings)
    payload = decode_token(token, settings=settings)
    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"
