"""
Multi-provider embedding factory.

Priority: OpenAI (text-embedding-3-small, 1536d)
        → Google Gemini (embedding-001, 768d)
        → Ollama (nomic-embed-text, 768d)

All three use LangChain providers already installed in the project — no new
heavyweight dependency (sentence-transformers) is needed.
"""
from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from app.core.settings import settings

logger = logging.getLogger(__name__)


@runtime_checkable
class EmbeddingProvider(Protocol):
    vector_size: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class _OpenAIProvider:
    vector_size = 1536

    def __init__(self) -> None:
        from langchain_openai import OpenAIEmbeddings
        self._impl = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key,  # type: ignore[arg-type]
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._impl.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._impl.embed_query(text)


class _GeminiProvider:
    vector_size = 768

    def __init__(self) -> None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        self._impl = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.gemini_api_key,  # type: ignore[arg-type]
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._impl.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._impl.embed_query(text)


class _OllamaProvider:
    vector_size = 768  # nomic-embed-text default

    def __init__(self) -> None:
        from langchain_ollama import OllamaEmbeddings
        self._impl = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=settings.ollama_base_url,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._impl.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._impl.embed_query(text)


def get_embedding_provider() -> EmbeddingProvider:
    """Return the first available embedding provider."""
    if settings.openai_api_key:
        try:
            p = _OpenAIProvider()
            logger.debug("Embedding provider: OpenAI text-embedding-3-small (1536d)")
            return p
        except Exception as exc:
            logger.warning("OpenAI embeddings unavailable: %s", exc)

    if settings.gemini_api_key:
        try:
            p = _GeminiProvider()
            logger.debug("Embedding provider: Google embedding-001 (768d)")
            return p
        except Exception as exc:
            logger.warning("Gemini embeddings unavailable: %s", exc)

    try:
        p = _OllamaProvider()
        logger.debug("Embedding provider: Ollama nomic-embed-text (768d)")
        return p
    except Exception as exc:
        raise RuntimeError(
            "No embedding provider available. Set OPENAI_API_KEY or GEMINI_API_KEY, "
            f"or run Ollama with `nomic-embed-text`. Last error: {exc}"
        ) from exc
