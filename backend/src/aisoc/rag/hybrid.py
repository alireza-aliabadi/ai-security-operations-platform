"""Hybrid keyword (BM25-ish) + vector search over the knowledge store."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from aisoc.core.logging import get_logger
from aisoc.rag.embeddings import get_embedding_provider
from aisoc.rag.qdrant_store import SearchHit, get_qdrant_store

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.-]{1,}", re.I)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    *,
    avgdl: float,
    df: Counter[str],
    n_docs: int,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    tf = Counter(doc_tokens)
    dl = len(doc_tokens)
    score = 0.0
    for term in query_tokens:
        if term not in tf:
            continue
        n_q = df.get(term, 0) or 1
        idf = math.log(1 + (n_docs - n_q + 0.5) / (n_q + 0.5))
        freq = tf[term]
        denom = freq + k1 * (1 - b + b * dl / (avgdl or 1.0))
        score += idf * (freq * (k1 + 1)) / (denom or 1.0)
    return score


def _hit_to_result(hit: SearchHit, *, keyword_score: float, vector_score: float) -> dict[str, Any]:
    payload = hit.payload
    content = str(payload.get("content") or "")
    snippet = content[:400] + ("…" if len(content) > 400 else "")
    combined = 0.45 * keyword_score + 0.55 * vector_score
    return {
        "id": hit.id,
        "title": payload.get("title") or "Untitled",
        "doc_type": payload.get("doc_type") or "unknown",
        "snippet": snippet,
        "content": content,
        "score": round(combined, 4),
        "keyword_score": round(keyword_score, 4),
        "vector_score": round(vector_score, 4),
        "metadata": payload.get("metadata") or {},
        "source_path": payload.get("source_path"),
    }


async def hybrid_search(
    query: str,
    *,
    limit: int = 8,
    doc_type: str | None = None,
    vector_weight: float = 0.55,
    keyword_weight: float = 0.45,
) -> list[dict[str, Any]]:
    """Combine BM25-ish keyword scores with vector similarity."""
    store = get_qdrant_store()
    embedder = get_embedding_provider()
    query_tokens = tokenize(query)

    filter_payload = {"doc_type": doc_type} if doc_type else None
    query_vector = await embedder.embed_one(query)
    vector_hits = store.search(
        query_vector,
        limit=max(limit * 5, 20),
        filter_payload=filter_payload,
    )

    # Build corpus stats from retrieved + in-memory payloads for BM25
    docs: list[tuple[SearchHit, list[str]]] = []
    for hit in vector_hits:
        text = " ".join(
            [
                str(hit.payload.get("title") or ""),
                str(hit.payload.get("content") or ""),
                str(hit.payload.get("doc_type") or ""),
            ]
        )
        docs.append((hit, tokenize(text)))

    n_docs = max(len(docs), 1)
    df: Counter[str] = Counter()
    total_len = 0
    for _, tokens in docs:
        total_len += len(tokens)
        df.update(set(tokens))
    avgdl = total_len / n_docs

    scored: list[dict[str, Any]] = []
    for hit, tokens in docs:
        kw = _bm25_score(query_tokens, tokens, avgdl=avgdl, df=df, n_docs=n_docs)
        # Normalize keyword roughly into 0..1 via sigmoid-ish squash
        kw_norm = kw / (1.0 + kw) if kw > 0 else 0.0
        vec = max(0.0, float(hit.score))
        combined = keyword_weight * kw_norm + vector_weight * vec
        result = _hit_to_result(hit, keyword_score=kw_norm, vector_score=vec)
        result["score"] = round(combined, 4)
        scored.append(result)

    # If store empty, still try keyword over nothing → empty
    scored.sort(key=lambda r: r["score"], reverse=True)
    logger.info("hybrid_search", query=query[:80], hits=len(scored), limit=limit)
    return scored[:limit]
