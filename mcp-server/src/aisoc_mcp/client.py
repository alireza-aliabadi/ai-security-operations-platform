"""HTTP client for AISOC backend APIs."""

from __future__ import annotations

from typing import Any

import httpx

from aisoc_mcp.config import MCPSettings, get_settings


class BackendClient:
    def __init__(self, settings: MCPSettings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = httpx.AsyncClient(
            base_url=self.settings.backend_internal_url.rstrip("/"),
            headers={"Authorization": f"Bearer {self.settings.mcp_api_token}"},
            timeout=self.settings.request_timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = await self._client.request(method, path, json=json, params=params)
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()

    async def search_logs(
        self,
        query: str = "*",
        *,
        platforms: list[str] | None = None,
        indices: list[str] | None = None,
        limit: int = 100,
    ) -> Any:
        return await self._request(
            "POST",
            "/api/v1/connectors/search",
            json={
                "query": query,
                "platforms": platforms,
                "indices": indices,
                "limit": limit,
            },
        )

    async def search_indices(self, query: str, indices: list[str], *, limit: int = 100) -> Any:
        return await self.search_logs(query, indices=indices, limit=limit)

    async def query_platform(self, query: str, platform: str, *, limit: int = 100) -> Any:
        return await self.search_logs(query, platforms=[platform], limit=limit)

    async def aggregate(
        self,
        query: str = "*",
        *,
        field: str = "severity",
        size: int = 10,
        platforms: list[str] | None = None,
    ) -> Any:
        return await self._request(
            "POST",
            "/api/v1/connectors/aggregate",
            json={"query": query, "field": field, "size": size, "platforms": platforms},
        )

    async def timeline(self, query: str = "*", *, platforms: list[str] | None = None, limit: int = 100) -> Any:
        return await self._request(
            "POST",
            "/api/v1/connectors/timeline",
            json={"query": query, "platforms": platforms, "limit": limit},
        )

    async def incident_summary(self, investigation_id: str) -> Any:
        return await self._request("GET", f"/api/v1/reports/{investigation_id}")

    async def lookup_ioc(self, value: str, ioc_type: str | None = None, text: str | None = None) -> Any:
        payload: dict[str, Any] = {}
        if text:
            payload["text"] = text
        elif ioc_type:
            payload["value"] = value
            payload["type"] = ioc_type
        else:
            payload["text"] = value
        return await self._request("POST", "/api/v1/threat-intel/enrich", json=payload)

    async def knowledge_search(self, query: str, *, limit: int = 8, doc_type: str | None = None) -> Any:
        return await self._request(
            "POST",
            "/api/v1/knowledge/search",
            json={"query": query, "limit": limit, "doc_type": doc_type},
        )

    async def runbook_search(self, query: str, *, limit: int = 8) -> Any:
        return await self.knowledge_search(query, limit=limit, doc_type="runbook")
