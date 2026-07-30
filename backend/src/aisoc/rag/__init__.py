"""RAG package — embeddings, Qdrant store, hybrid search, and ingestion."""

from aisoc.rag.embeddings import EmbeddingProvider, get_embedding_provider, hash_embed
from aisoc.rag.hybrid import hybrid_search
from aisoc.rag.ingest import ingest_seed_knowledge
from aisoc.rag.qdrant_store import QdrantStore, get_qdrant_store

__all__ = [
    "EmbeddingProvider",
    "QdrantStore",
    "get_embedding_provider",
    "get_qdrant_store",
    "hash_embed",
    "hybrid_search",
    "ingest_seed_knowledge",
]
