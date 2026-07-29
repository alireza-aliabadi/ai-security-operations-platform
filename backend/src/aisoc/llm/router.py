"""LLM router with primary → local → mock fallback."""

from __future__ import annotations

from typing import Any

from aisoc.core.config import Settings, get_settings
from aisoc.core.logging import get_logger
from aisoc.llm.cost import CostTracker
from aisoc.llm.mock import MockLLM
from aisoc.llm.ollama import OllamaClient
from aisoc.llm.openai_compat import OpenAICompatClient

logger = get_logger(__name__)


class LLMRouter:
    """Routes chat/embed calls through a configured fallback order."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.cost = CostTracker()
        self.last_provider: str | None = None
        self.last_model: str | None = None
        self._primary = OpenAICompatClient(
            base_url=self.settings.llm_primary_base_url,
            api_key=self.settings.llm_primary_api_key,
            model=self.settings.llm_primary_model,
            embedding_model=self.settings.llm_embedding_model,
            provider_name="primary",
        )
        self._local = OllamaClient()
        self._mock = MockLLM()

    def _providers(self) -> list[tuple[str, Any]]:
        mapping = {
            "primary": self._primary,
            "local": self._local,
            "mock": self._mock,
        }
        order = self.settings.llm_providers or ["primary", "local", "mock"]
        providers: list[tuple[str, Any]] = []
        for name in order:
            client = mapping.get(name)
            if client is not None:
                providers.append((name, client))
        # Ensure mock is always available as last resort
        if "mock" not in {n for n, _ in providers}:
            providers.append(("mock", self._mock))
        return providers

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        temp = self.settings.llm_temperature if temperature is None else temperature
        tokens = self.settings.llm_max_tokens if max_tokens is None else max_tokens
        errors: list[str] = []

        for name, client in self._providers():
            if name == "primary" and not self.settings.llm_primary_api_key:
                errors.append("primary: missing api key")
                continue
            try:
                result = await client.chat(messages, temperature=temp, max_tokens=tokens)
                self.last_provider = result.get("provider", name)
                self.last_model = result.get("model")
                prompt = "\n".join(m.get("content", "") for m in messages)
                self.cost.record_chat(
                    model=str(self.last_model or "unknown"),
                    prompt=prompt,
                    completion=str(result.get("content") or ""),
                    provider=str(self.last_provider),
                )
                logger.info("llm_chat_ok", provider=self.last_provider, model=self.last_model)
                return result
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name}: {exc}")
                logger.warning("llm_chat_fallback", provider=name, error=str(exc))

        # Absolute fallback
        result = await self._mock.chat(messages, temperature=temp, max_tokens=tokens)
        self.last_provider = "mock"
        self.last_model = result.get("model")
        prompt = "\n".join(m.get("content", "") for m in messages)
        self.cost.record_chat(
            model=str(self.last_model or "mock"),
            prompt=prompt,
            completion=str(result.get("content") or ""),
            provider="mock",
        )
        result["fallback_errors"] = errors
        return result

    async def embed(self, texts: list[str] | str) -> dict[str, Any]:
        errors: list[str] = []
        for name, client in self._providers():
            if name == "primary" and not self.settings.llm_primary_api_key:
                errors.append("primary: missing api key")
                continue
            try:
                result = await client.embed(texts)
                self.last_provider = result.get("provider", name)
                self.last_model = result.get("model")
                blob = texts if isinstance(texts, str) else "\n".join(texts)
                self.cost.record_embed(
                    model=str(self.last_model or "unknown"),
                    text=blob,
                    provider=str(self.last_provider),
                )
                return result
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name}: {exc}")
                logger.warning("llm_embed_fallback", provider=name, error=str(exc))

        result = await self._mock.embed(texts)
        self.last_provider = "mock"
        self.last_model = result.get("model")
        blob = texts if isinstance(texts, str) else "\n".join(texts)
        self.cost.record_embed(
            model=str(self.last_model or "mock"),
            text=blob,
            provider="mock",
        )
        result["fallback_errors"] = errors
        return result


_router: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
