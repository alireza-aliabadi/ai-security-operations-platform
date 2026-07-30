"""Local Ollama client via OpenAI-compatible API."""

from __future__ import annotations

from aisoc.core.config import get_settings
from aisoc.llm.openai_compat import OpenAICompatClient


class OllamaClient(OpenAICompatClient):
    """OpenAI-compat client pointed at a local Ollama base URL."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        settings = get_settings()
        super().__init__(
            base_url=base_url or settings.llm_local_base_url,
            api_key=api_key if api_key is not None else settings.llm_local_api_key,
            model=model or settings.llm_local_model,
            embedding_model=embedding_model or settings.llm_embedding_model,
            timeout=timeout,
            provider_name="local",
        )
