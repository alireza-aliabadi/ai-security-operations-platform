"""Integration tests for password login against seeded users."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_seed_analyst(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "analyst@aisoc.local",
            "password": "ChangeMeAnalyst123!",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] > 0

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    profile = me.json()
    assert profile["email"] == "analyst@aisoc.local"
    assert "analyst" in profile["roles"]
    assert "chat:use" in profile["permissions"]


@pytest.mark.asyncio
async def test_login_rejects_bad_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@aisoc.local", "password": "not-the-password"},
    )
    assert response.status_code == 401
