"""
RAG agent: retrieve relevant chunks from Qdrant, then generate a grounded answer.

Falls back to a structured excerpt summary when no LLM is available so the
endpoint always returns something useful.
"""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, SearchHit, SearchRequest
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

_SYSTEM = (
    "You are a precise assistant. Answer the user's question using ONLY the provided "
    "context chunks. If the context is insufficient, say so explicitly. "
    "Cite source numbers (e.g. [1], [2]) when referencing chunks. "
    "Be concise. Respond in the same language as the question."
)


class RAGAgent:
    def __init__(self) -> None:
        self._svc = RAGService()

    def query(self, req: RAGQueryRequest) -> RAGQueryResponse:
        search_resp = self._svc.search(
            SearchRequest(
                collection=req.collection,
                query=req.question,
                top_k=req.top_k,
                score_threshold=req.score_threshold,
            )
        )

        if not search_resp.hits:
            return RAGQueryResponse(
                collection=req.collection,
                question=req.question,
                answer=(
                    "No se encontraron documentos relevantes en la colección "
                    f"'{req.collection}' para esta pregunta."
                ),
                sources=[],
                retrieved=0,
            )

        context = _build_context(search_resp.hits)
        answer  = _generate(req.question, context) or _fallback_answer(search_resp.hits)

        return RAGQueryResponse(
            collection=req.collection,
            question=req.question,
            answer=answer,
            sources=search_resp.hits,
            retrieved=len(search_resp.hits),
        )


def _build_context(hits: list[SearchHit]) -> str:
    return "\n\n".join(
        f"[{i + 1}] (score={h.score:.3f})\n{h.text}"
        for i, h in enumerate(hits)
    )


def _generate(question: str, context: str) -> str | None:
    llm = get_llm("general")
    if llm is None:
        return None
    try:
        messages = [
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
        ]
        response = llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.warning("LLM failed in RAG query: %s", exc)
        return None


def _fallback_answer(hits: list[SearchHit]) -> str:
    excerpts = "\n".join(
        f"[{i + 1}] (score={h.score:.3f}) {h.text[:200]}…"
        for i, h in enumerate(hits[:3])
    )
    return f"Fragmentos más relevantes encontrados:\n\n{excerpts}"
