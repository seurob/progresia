"""
RAG service: orchestrates text chunking, embedding, indexing, retrieval and evaluation.

Chunking strategy: fixed word-count windows with overlap. Intentionally simple —
avoids sentence-transformers or NLTK and keeps the dependency footprint minimal.
"""
from __future__ import annotations

import logging
import uuid

from app.core.embeddings import get_embedding_provider
from app.core.qdrant import (
    collection_count,
    delete_collection,
    ensure_collection,
    get_qdrant_client,
    scroll_sample,
    search_points,
    upsert_points,
)
from app.schemas.rag import (
    EvalReport,
    EvalSample,
    IndexRequest,
    IndexResponse,
    SearchHit,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)

_EVAL_THRESHOLD = 0.5
_EVAL_QUERY_WORDS = 40  # first N words of a chunk become the eval query


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


class RAGService:
    def index(self, req: IndexRequest) -> IndexResponse:
        provider = get_embedding_provider()
        client   = get_qdrant_client()

        texts: list[str]             = []
        payloads: list[dict]         = []
        ids: list[str]               = []

        for doc in req.documents:
            chunks = _chunk_text(doc.text, req.chunk_size, req.chunk_overlap)
            for i, chunk in enumerate(chunks):
                stable_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc.id}__chunk{i}"))
                texts.append(chunk)
                payloads.append({
                    "text": chunk,
                    "doc_id": doc.id,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                    **doc.metadata,
                })
                ids.append(stable_id)

        if not texts:
            return IndexResponse(collection=req.collection, indexed=0, chunks=0)

        ensure_collection(client, req.collection, provider.vector_size)
        vectors  = provider.embed_documents(texts)
        upserted = upsert_points(client, req.collection, vectors, payloads, ids)

        logger.info(
            "Indexed %d documents → %d chunks into collection '%s'",
            len(req.documents), upserted, req.collection,
        )
        return IndexResponse(
            collection=req.collection,
            indexed=len(req.documents),
            chunks=upserted,
        )

    def search(self, req: SearchRequest) -> SearchResponse:
        provider  = get_embedding_provider()
        client    = get_qdrant_client()
        query_vec = provider.embed_query(req.query)
        raw = search_points(
            client, req.collection, query_vec,
            req.top_k, req.score_threshold, req.metadata_filter,
        )
        hits = [
            SearchHit(id=r["id"], text=r["text"], score=r["score"], metadata=r["metadata"])
            for r in raw
        ]
        return SearchResponse(collection=req.collection, query=req.query, hits=hits)

    def eval(self, collection: str, top_k: int = 5) -> EvalReport:
        """Self-consistency evaluation: use a prefix of each chunk as its own query
        and check whether the chunk re-surfaces near the top of results."""
        provider = get_embedding_provider()
        client   = get_qdrant_client()
        total    = collection_count(client, collection)
        raw_docs = scroll_sample(client, collection, limit=20)

        samples: list[EvalSample] = []
        for doc in raw_docs:
            text = doc["text"]
            if not text:
                continue
            query = " ".join(text.split()[:_EVAL_QUERY_WORDS])
            query_vec = provider.embed_query(query)
            results   = search_points(client, collection, query_vec, top_k, 0.0)
            top_score = results[0]["score"] if results else 0.0
            hit = any(r["id"] == doc["id"] for r in results)
            samples.append(EvalSample(
                doc_id=doc["id"],
                query=query[:100],
                top_score=top_score,
                hit=hit,
            ))

        if not samples:
            return EvalReport(
                collection=collection,
                total_documents=total,
                samples_tested=0,
                hit_rate=0.0,
                mean_top_score=0.0,
                threshold_used=_EVAL_THRESHOLD,
                samples=[],
            )

        hit_rate   = sum(1 for s in samples if s.top_score >= _EVAL_THRESHOLD) / len(samples)
        mean_score = sum(s.top_score for s in samples) / len(samples)

        return EvalReport(
            collection=collection,
            total_documents=total,
            samples_tested=len(samples),
            hit_rate=round(hit_rate, 4),
            mean_top_score=round(mean_score, 4),
            threshold_used=_EVAL_THRESHOLD,
            samples=samples,
        )

    def delete(self, collection: str) -> bool:
        return delete_collection(get_qdrant_client(), collection)
