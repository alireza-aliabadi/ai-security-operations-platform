"""Threat intelligence enrichment service with optional Redis cache."""

from __future__ import annotations

import json
from typing import Any

from aisoc.core.config import Settings, get_settings
from aisoc.core.logging import get_logger
from aisoc.threat_intel.extractors import extract_iocs, flatten_iocs
from aisoc.threat_intel.providers import ThreatIntelProvider, default_providers

logger = get_logger(__name__)

CACHE_TTL_SECONDS = 3600


class _MemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        _ = ex
        self._data[key] = value


class EnrichmentService:
    def __init__(
        self,
        providers: list[ThreatIntelProvider] | None = None,
        settings: Settings | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.providers = providers or default_providers()
        self._redis = redis_client
        self._memory = _MemoryCache()
        self._redis_failed = False

    async def _cache(self) -> Any:
        if self._redis_failed:
            return self._memory
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as redis

            client = redis.from_url(self.settings.redis_url, decode_responses=True)
            await client.ping()
            self._redis = client
            return self._redis
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis_cache_unavailable", error=str(exc))
            self._redis_failed = True
            self._redis = None
            return self._memory

    def _cache_key(self, ioc_type: str, value: str) -> str:
        return f"aisoc:ti:{ioc_type}:{value.lower()}"

    async def enrich_one(self, ioc_type: str, value: str) -> dict[str, Any]:
        cache = await self._cache()
        key = self._cache_key(ioc_type, value)
        try:
            cached = await cache.get(key)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception as exc:  # noqa: BLE001
            logger.warning("ti_cache_get_failed", error=str(exc))

        provider_results: list[dict[str, Any]] = []
        for provider in self.providers:
            try:
                result = await provider.enrich(ioc_type, value)
                provider_results.append(result)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "ti_provider_failed",
                    provider=getattr(provider, "name", "?"),
                    error=str(exc),
                )

        scores = [int(r.get("score") or 0) for r in provider_results if r.get("supported", True)]
        max_score = max(scores) if scores else 0
        malicious = any(bool(r.get("malicious")) for r in provider_results)
        labels: list[str] = []
        for r in provider_results:
            labels.extend(str(x) for x in (r.get("labels") or []))
        labels = sorted(set(labels))

        enriched = {
            "type": ioc_type,
            "value": value,
            "malicious": malicious,
            "score": max_score,
            "labels": labels,
            "providers": provider_results,
            "cached": False,
        }
        try:
            await cache.set(key, json.dumps(enriched), ex=CACHE_TTL_SECONDS)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ti_cache_set_failed", error=str(exc))
        return enriched

    async def enrich_iocs(
        self,
        iocs: dict[str, list[str]] | list[dict[str, str]] | str | list[str] | None = None,
        *,
        text: str | None = None,
    ) -> dict[str, Any]:
        """Enrich IOC dict/list or extract+enrich from text."""
        if text is not None:
            iocs = extract_iocs(text)
        if iocs is None:
            iocs = {}

        if isinstance(iocs, str):
            iocs = extract_iocs(iocs)

        items: list[dict[str, str]]
        if isinstance(iocs, list):
            # list of strings → extract, or list of {type,value}
            if iocs and isinstance(iocs[0], str):
                extracted = extract_iocs([str(x) for x in iocs])  # type: ignore[arg-type]
                items = flatten_iocs(extracted)
            else:
                items = [{"type": str(i["type"]), "value": str(i["value"])} for i in iocs]  # type: ignore[index]
        else:
            items = flatten_iocs(iocs)

        enriched_items: list[dict[str, Any]] = []
        for item in items:
            enriched_items.append(await self.enrich_one(item["type"], item["value"]))

        by_type: dict[str, list[dict[str, Any]]] = {
            "ip": [],
            "domain": [],
            "hash": [],
            "cve": [],
        }
        for item in enriched_items:
            bucket = by_type.setdefault(item["type"], [])
            bucket.append(item)

        return {
            "items": enriched_items,
            "by_type": by_type,
            "summary": {
                "total": len(enriched_items),
                "malicious": sum(1 for i in enriched_items if i.get("malicious")),
                "max_score": max((int(i.get("score") or 0) for i in enriched_items), default=0),
            },
        }


_service: EnrichmentService | None = None


def get_enrichment_service() -> EnrichmentService:
    global _service
    if _service is None:
        _service = EnrichmentService()
    return _service


async def enrich_iocs(
    iocs: dict[str, list[str]] | list[dict[str, str]] | str | list[str] | None = None,
    *,
    text: str | None = None,
) -> dict[str, Any]:
    return await get_enrichment_service().enrich_iocs(iocs, text=text)
