from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RagDocument(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexRequest(BaseModel):
    collection: str
    documents: list[RagDocument]
    chunk_size: int = Field(default=400, ge=50, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=200)


class IndexResponse(BaseModel):
    collection: str
    indexed: int
    chunks: int


class SearchRequest(BaseModel):
    collection: str
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata_filter: dict[str, Any] | None = None


class SearchHit(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    collection: str
    query: str
    hits: list[SearchHit]


class RAGQueryRequest(BaseModel):
    collection: str
    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    collection: str
    question: str
    answer: str
    sources: list[SearchHit]
    retrieved: int


class EvalSample(BaseModel):
    doc_id: str
    query: str
    top_score: float
    hit: bool


class EvalReport(BaseModel):
    collection: str
    total_documents: int
    samples_tested: int
    hit_rate: float
    mean_top_score: float
    threshold_used: float
    samples: list[EvalSample]
