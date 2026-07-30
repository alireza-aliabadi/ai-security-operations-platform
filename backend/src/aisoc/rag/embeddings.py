"""Embedding provider with LLM router and deterministic hash fallback."""

from __future__ import annotations

import hashlib
import math
from typing import Any

from aisoc.core.logging import get_logger
from aisoc.llm.router import LLMRouter, get_llm_router

logger = get_logger(__name__)

EMBEDDING_DIM = 384


def hash_embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic unit-normalized embedding from hashlib (mock fallback)."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dim:
        for b in digest:
            values.append((b / 255.0) * 2 - 1)
            if len(values) >= dim:
                break
        digest = hashlib.sha256(digest).digest()
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def _normalize_dim(vector: list[float], dim: int = EMBEDDING_DIM) -> list[float]:
    if len(vector) == dim:
        return vector
    if len(vector) > dim:
        vector = vector[:dim]
    else:
        vector = vector + [0.0] * (dim - len(vector))
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


class EmbeddingProvider:
    """Embed texts via LLMRouter.embed, falling back to hash vectors."""

    def __init__(self, router: LLMRouter | None = None, dim: int = EMBEDDING_DIM) -> None:
        self.router = router or get_llm_router()
        self.dim = dim

    async def embed(self, texts: list[str] | str) -> list[list[float]]:
        input_texts = [texts] if isinstance(texts, str) else list(texts)
        if not input_texts:
            return []
        try:
            result: dict[str, Any] = await self.router.embed(input_texts)
            embeddings = result.get("embeddings") or []
            if embeddings and len(embeddings) == len(input_texts):
                return [_normalize_dim(list(v), self.dim) for v in embeddings]
            logger.warning("embed_unexpected_shape", count=len(embeddings))
        except Exception as exc:  # noqa: BLE001
            logger.warning("embed_router_failed", error=str(exc))
        return [hash_embed(t, self.dim) for t in input_texts]

    async def embed_one(self, text: str) -> list[float]:
        vectors = await self.embed(text)
        return vectors[0] if vectors else hash_embed(text, self.dim)


_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        _provider = EmbeddingProvider()
    return _provider
