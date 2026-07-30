"""OpenAI-compatible chat and embeddings client (httpx)."""

from __future__ import annotations

from typing import Any

import httpx

from aisoc.core.logging import get_logger

logger = get_logger(__name__)


class OpenAICompatClient:
    """Minimal OpenAI-compatible HTTP client for chat and embeddings."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        embedding_model: str | None = None,
        timeout: float = 60.0,
        provider_name: str = "primary",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model or model
        self.provider_name = provider_name
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        model: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        content = ""
        choices = data.get("choices") or []
        if choices:
            content = (choices[0].get("message") or {}).get("content") or ""
        return {
            "content": content,
            "raw": data,
            "provider": self.provider_name,
            "model": payload["model"],
        }

    async def embed(
        self,
        texts: list[str] | str,
        *,
        model: str | None = None,
    ) -> dict[str, Any]:
        input_texts = [texts] if isinstance(texts, str) else list(texts)
        payload = {
            "model": model or self.embedding_model,
            "input": input_texts,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        vectors = [item.get("embedding", []) for item in data.get("data") or []]
        return {
            "embeddings": vectors,
            "raw": data,
            "provider": self.provider_name,
            "model": payload["model"],
        }

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                return response.status_code < 500
        except Exception:  # noqa: BLE001
            return False
