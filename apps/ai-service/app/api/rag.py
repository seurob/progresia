"""RAG (Retrieval-Augmented Generation) endpoints: index, search, query,
evaluate, and delete Qdrant collections."""
from __future__ import annotations

from fastapi import APIRouter, Response

from app.agents.rag_agent import RAGAgent
from app.schemas.rag import (
    IndexRequest,
    IndexResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/rag")


@router.post("/index", status_code=201, response_model=IndexResponse)
def rag_index(payload: IndexRequest) -> IndexResponse:
    """Chunk, embed and index documents into a named Qdrant collection."""
    return RAGService().index(payload)


@router.post("/search", response_model=SearchResponse)
def rag_search(payload: SearchRequest) -> SearchResponse:
    """Semantic search: embed the query and return the top-k similar chunks."""
    return RAGService().search(payload)


@router.post("/query", response_model=RAGQueryResponse)
def rag_query(payload: RAGQueryRequest) -> RAGQueryResponse:
    """RAG pipeline: retrieve relevant chunks, then generate a grounded answer."""
    return RAGAgent().query(payload)


@router.get("/eval/{collection}")
def rag_eval(collection: str, top_k: int = 5):
    """Self-consistency evaluation: sample chunks, use their prefix as query,
    measure how often the original chunk surfaces in top-k results."""
    return RAGService().eval(collection, top_k)


@router.delete("/collection/{collection}", status_code=204)
def rag_delete_collection(collection: str) -> Response:
    """Delete a Qdrant collection and all its indexed vectors."""
    RAGService().delete(collection)
    return Response(status_code=204)
