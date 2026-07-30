"""Unit tests for hybrid RAG search over an in-memory vector store."""

from __future__ import annotations

import pytest

from aisoc.core.config import Settings
from aisoc.rag import hybrid as hybrid_mod
from aisoc.rag import qdrant_store as store_mod
from aisoc.rag.embeddings import hash_embed
from aisoc.rag.qdrant_store import QdrantStore


@pytest.mark.asyncio
async def test_hybrid_search_with_in_memory_store() -> None:
    settings = Settings(
        app_env="test",
        secret_key="test-secret-key-at-least-32-characters-long!!",
        encryption_key="0123456789abcdef0123456789abcdef",
        llm_primary_api_key="",
        qdrant_url="http://127.0.0.1:9",  # force unreachable → memory
        qdrant_collection="aisoc_test_knowledge",
    )
    store = QdrantStore(settings=settings)
    store._use_memory = True
    store._client = None
    store_mod._store = store

    docs = [
        {
            "id": "doc-1",
            "vector": hash_embed("brute force authentication failures runbook"),
            "payload": {
                "title": "Brute Force Detection Runbook",
                "doc_type": "runbook",
                "content": (
                    "Confirm failed authentication spikes. Extract source IPs. "
                    "Contain malicious IPs after brute force attempts."
                ),
            },
        },
        {
            "id": "doc-2",
            "vector": hash_embed("c2 containment malware beacon"),
            "payload": {
                "title": "C2 Containment SOP",
                "doc_type": "sop",
                "content": "Watch for C2 indicators such as 185.220.101.45 and evil.example.com.",
            },
        },
    ]
    store.upsert(docs)

    results = await hybrid_mod.hybrid_search("brute force authentication", limit=5)
    assert results
    assert any("brute" in r["title"].lower() or "brute" in r["content"].lower() for r in results)
    assert results[0]["score"] >= 0
