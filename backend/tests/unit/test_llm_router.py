"""Unit tests for LLM router mock fallback when no API keys are set."""

from __future__ import annotations

import pytest

from aisoc.core.config import Settings
from aisoc.llm.router import LLMRouter


@pytest.mark.asyncio
async def test_mock_provider_used_when_no_keys() -> None:
    settings = Settings(
        app_env="test",
        secret_key="test-secret-key-at-least-32-characters-long!!",
        encryption_key="0123456789abcdef0123456789abcdef",
        llm_primary_api_key="",
        llm_fallback_order="primary,local,mock",
    )
    router = LLMRouter(settings=settings)
    result = await router.chat(
        [
            {"role": "system", "content": "Extract keywords as JSON"},
            {"role": "user", "content": "Investigate brute force and C2 to 185.220.101.45"},
        ]
    )
    assert result["provider"] == "mock"
    assert router.last_provider == "mock"
    assert result.get("content")
    assert "keywords" in str(result["content"]).lower() or "severity" in str(result["content"]).lower()
