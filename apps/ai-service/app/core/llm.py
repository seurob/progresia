"""
Multi-provider LLM factory with task-aware routing.

Task routing strategy:
  reasoning  → Groq (llama-3.3-70b) → OpenAI → Gemini → Ollama (llama3.1)  → None
  code       → Ollama (qwen2.5-coder) → Groq  → OpenAI → None
  spec       → OpenAI → Gemini → Groq → Ollama (llama3.1) → None
  general    → Groq   → OpenAI → Gemini → Ollama → None

Each step is tried in order; a missing key or import error skips to the next.
"""
from __future__ import annotations

import logging
from typing import Callable, Literal

from langchain_core.language_models import BaseChatModel

from app.core.settings import settings

logger = logging.getLogger(__name__)

TaskType = Literal["reasoning", "code", "spec", "general"]


# ── Individual provider constructors ─────────────────────────────────────────

def _groq(model: str | None = None) -> BaseChatModel | None:
    if not settings.groq_api_key:
        return None
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model or settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0,
        )
    except Exception as exc:
        logger.debug("Groq unavailable: %s", exc)
        return None


def _openai(model: str | None = None) -> BaseChatModel | None:
    if not settings.openai_api_key:
        return None
    try:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
        )
    except Exception as exc:
        logger.debug("OpenAI unavailable: %s", exc)
        return None


def _gemini(model: str | None = None) -> BaseChatModel | None:
    if not settings.gemini_api_key:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model or settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0,
        )
    except Exception as exc:
        logger.debug("Gemini unavailable: %s", exc)
        return None


def _ollama(model: str) -> BaseChatModel | None:
    try:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
    except Exception as exc:
        logger.debug("Ollama unavailable: %s", exc)
        return None


# ── Task-aware routing ────────────────────────────────────────────────────────

_TASK_CHAINS: dict[str, list[Callable[[], BaseChatModel | None]]] = {
    # Fast structured analysis; Groq excels here
    "reasoning": [
        lambda: _groq(),
        lambda: _openai(),
        lambda: _gemini(),
        lambda: _ollama(settings.ollama_reasoning_model),
    ],
    # Code generation; qwen2.5-coder is purpose-built for code
    "code": [
        lambda: _ollama(settings.ollama_code_model),
        lambda: _groq(),
        lambda: _openai(),
        lambda: _gemini(),
    ],
    # Complex structured specs; GPT-4o-mini / Gemini handle large schemas better
    "spec": [
        lambda: _openai(),
        lambda: _gemini(),
        lambda: _groq(),
        lambda: _ollama(settings.ollama_reasoning_model),
    ],
    # General: follow llm_provider setting order
    "general": [
        lambda: _groq(),
        lambda: _openai(),
        lambda: _gemini(),
        lambda: _ollama(settings.ollama_reasoning_model),
    ],
}


def get_llm(task: TaskType = "general") -> BaseChatModel | None:
    """Return the first available LLM for the given task type.

    Falls back through the provider chain automatically so callers
    never need to know which API key is configured.
    """
    for factory in _TASK_CHAINS.get(task, _TASK_CHAINS["general"]):
        llm = factory()
        if llm is not None:
            logger.debug("LLM resolved for task=%s: %s", task, type(llm).__name__)
            return llm
    logger.warning("No LLM available for task=%s — deterministic fallback active", task)
    return None
