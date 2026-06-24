"""
Qdrant client utilities: singleton, collection management, upsert and search.
"""
from __future__ import annotations

import logging
import uuid
from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.settings import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    client = QdrantClient(url=settings.qdrant_url, timeout=10)
    logger.info("Qdrant client connected to %s", settings.qdrant_url)
    return client


def ensure_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection '%s' (vector_size=%d)", name, vector_size)


def upsert_points(
    client: QdrantClient,
    collection: str,
    vectors: list[list[float]],
    payloads: list[dict[str, Any]],
    ids: list[str] | None = None,
) -> int:
    point_ids = ids or [str(uuid.uuid4()) for _ in vectors]
    points = [
        PointStruct(id=pid, vector=vec, payload=pay)
        for pid, vec, pay in zip(point_ids, vectors, payloads)
    ]
    client.upsert(collection_name=collection, points=points, wait=True)
    return len(points)


def search_points(
    client: QdrantClient,
    collection: str,
    query_vector: list[float],
    top_k: int = 5,
    score_threshold: float = 0.0,
    metadata_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    qdrant_filter: Filter | None = None
    if metadata_filter:
        qdrant_filter = Filter(
            must=[
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in metadata_filter.items()
            ]
        )

    results = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold if score_threshold > 0 else None,
        query_filter=qdrant_filter,
        with_payload=True,
    )

    return [
        {
            "id": str(r.id),
            "score": r.score,
            "text": (r.payload or {}).get("text", ""),
            "metadata": {k: v for k, v in (r.payload or {}).items() if k != "text"},
        }
        for r in results
    ]


def collection_count(client: QdrantClient, collection: str) -> int:
    try:
        return client.get_collection(collection).points_count or 0
    except Exception:
        return 0


def scroll_sample(
    client: QdrantClient, collection: str, limit: int = 20
) -> list[dict[str, Any]]:
    points, _ = client.scroll(
        collection_name=collection,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [
        {
            "id": str(p.id),
            "text": (p.payload or {}).get("text", ""),
            "metadata": {k: v for k, v in (p.payload or {}).items() if k != "text"},
        }
        for p in points
    ]


def delete_collection(client: QdrantClient, collection: str) -> bool:
    try:
        client.delete_collection(collection)
        logger.info("Deleted Qdrant collection '%s'", collection)
        return True
    except Exception as exc:
        logger.warning("Failed to delete collection '%s': %s", collection, exc)
        return False
