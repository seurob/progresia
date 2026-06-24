"""
Multi-provider LLM factory with task-aware routing and runtime overrides.

Task routing strategy (default — no override):
  reasoning  → Groq (llama-3.3-70b) → OpenAI → Gemini → Ollama (llama3.1)
  code       → Ollama (qwen2.5-coder) → Groq  → OpenAI → Gemini
  spec       → OpenAI → Gemini → Groq → Ollama (llama3.1)
  general    → Groq   → OpenAI → Gemini → Ollama

If override_provider is set via apply_config_update(), all tasks use that
provider first; on failure they fall through to the normal task chain.
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Literal

from langchain_core.language_models import BaseChatModel

from app.core.settings import settings

logger = logging.getLogger(__name__)

TaskType = Literal["reasoning", "code", "spec", "general"]

# ── Runtime overrides (reset on process restart) ──────────────────────────────
_lock = threading.Lock()
_override_provider: str | None = None
_model_overrides: dict[str, str] = {}


def _eff(key: str, default: str) -> str:
    """Return the effective model: runtime override if set, otherwise the default."""
    return _model_overrides.get(key, default)


# ── Individual provider constructors ─────────────────────────────────────────

def _groq(model: str | None = None) -> BaseChatModel | None:
    if not settings.groq_api_key:
        return None
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=model or _eff("groq_model", settings.groq_model),
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
            model=model or _eff("openai_model", settings.openai_model),
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
            model=model or _eff("gemini_model", settings.gemini_model),
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
    "reasoning": [
        lambda: _groq(),
        lambda: _openai(),
        lambda: _gemini(),
        lambda: _ollama(_eff("ollama_reasoning_model", settings.ollama_reasoning_model)),
    ],
    "code": [
        lambda: _ollama(_eff("ollama_code_model", settings.ollama_code_model)),
        lambda: _groq(),
        lambda: _openai(),
        lambda: _gemini(),
    ],
    "spec": [
        lambda: _openai(),
        lambda: _gemini(),
        lambda: _groq(),
        lambda: _ollama(_eff("ollama_reasoning_model", settings.ollama_reasoning_model)),
    ],
    "general": [
        lambda: _groq(),
        lambda: _openai(),
        lambda: _gemini(),
        lambda: _ollama(_eff("ollama_reasoning_model", settings.ollama_reasoning_model)),
    ],
}


def get_llm(task: TaskType = "general") -> BaseChatModel | None:
    """Return the first available LLM for the given task type.

    If override_provider is set, it is tried first; on failure falls
    through to the normal task-based chain automatically.
    """
    if _override_provider:
        llm: BaseChatModel | None = None
        if _override_provider == "groq":
            llm = _groq()
        elif _override_provider == "openai":
            llm = _openai()
        elif _override_provider == "gemini":
            llm = _gemini()
        elif _override_provider == "ollama":
            model = (
                _eff("ollama_code_model", settings.ollama_code_model)
                if task == "code"
                else _eff("ollama_reasoning_model", settings.ollama_reasoning_model)
            )
            llm = _ollama(model)
        if llm is not None:
            logger.debug("LLM via override=%s task=%s", _override_provider, task)
            return llm
        logger.warning("Override provider %s failed, falling back to task routing", _override_provider)

    for factory in _TASK_CHAINS.get(task, _TASK_CHAINS["general"]):
        llm = factory()
        if llm is not None:
            logger.debug("LLM resolved for task=%s: %s", task, type(llm).__name__)
            return llm

    logger.warning("No LLM available for task=%s — deterministic fallback active", task)
    return None


# ── Config state helpers (used by /config/llm endpoint) ──────────────────────

def get_config_state() -> dict:
    """Snapshot of the current LLM configuration — no LLM instances created."""
    has_groq = bool(settings.groq_api_key)
    has_openai = bool(settings.openai_api_key)
    has_gemini = bool(settings.gemini_api_key)

    def resolve(chain: list[tuple[str, bool]]) -> str:
        if _override_provider:
            return _override_provider
        for name, available in chain:
            if available:
                return name
        return "none"

    return {
        "override_provider": _override_provider,
        "ollama_base_url": settings.ollama_base_url,
        "providers": [
            {
                "name": "groq",
                "has_key": has_groq,
                "model": _eff("groq_model", settings.groq_model),
                "default_model": settings.groq_model,
            },
            {
                "name": "openai",
                "has_key": has_openai,
                "model": _eff("openai_model", settings.openai_model),
                "default_model": settings.openai_model,
            },
            {
                "name": "gemini",
                "has_key": has_gemini,
                "model": _eff("gemini_model", settings.gemini_model),
                "default_model": settings.gemini_model,
            },
            {
                "name": "ollama",
                "has_key": True,
                "model": _eff("ollama_reasoning_model", settings.ollama_reasoning_model),
                "default_model": settings.ollama_reasoning_model,
                "code_model": _eff("ollama_code_model", settings.ollama_code_model),
                "default_code_model": settings.ollama_code_model,
            },
        ],
        "task_routing": {
            "reasoning": resolve([
                ("groq", has_groq), ("openai", has_openai), ("gemini", has_gemini), ("ollama", True),
            ]),
            "code": resolve([
                ("ollama", True), ("groq", has_groq), ("openai", has_openai), ("gemini", has_gemini),
            ]),
            "spec": resolve([
                ("openai", has_openai), ("gemini", has_gemini), ("groq", has_groq), ("ollama", True),
            ]),
            "general": resolve([
                ("groq", has_groq), ("openai", has_openai), ("gemini", has_gemini), ("ollama", True),
            ]),
        },
    }


def apply_config_update(update: object) -> None:
    """Thread-safe apply of a LLMConfigUpdate payload to the runtime state."""
    global _override_provider, _model_overrides

    with _lock:
        if "override_provider" in getattr(update, "model_fields_set", set()):
            _override_provider = update.override_provider  # type: ignore[attr-defined]

        if getattr(update, "reset_models", False):
            _model_overrides.clear()

        for key in (
            "groq_model",
            "openai_model",
            "gemini_model",
            "ollama_reasoning_model",
            "ollama_code_model",
        ):
            val = getattr(update, key, None)
            if val is not None:
                _model_overrides[key] = val
