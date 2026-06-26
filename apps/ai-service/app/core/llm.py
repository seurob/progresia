"""
Multi-provider LLM factory with task-aware routing and runtime overrides.

Task routing strategy (default — no override):
  reasoning  → Groq (llama-3.3-70b) → OpenAI → Gemini → Ollama (Gemma 4)
  code       → Ollama (Gemma 4) → Groq → OpenAI → Gemini
  spec       → OpenAI → Gemini → Groq → Ollama (Gemma 4)
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
_DEFAULT_CLOUD_ORDER = ("groq", "openai", "gemini")
_cloud_order: list[str] = list(_DEFAULT_CLOUD_ORDER)


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
            reasoning=False,
        )
    except Exception as exc:
        logger.debug("Ollama unavailable: %s", exc)
        return None


# ── Task-aware routing ────────────────────────────────────────────────────────

_CLOUD_FACTORIES: dict[str, Callable[[], BaseChatModel | None]] = {
    "groq": _groq,
    "openai": _openai,
    "gemini": _gemini,
}


def _get_task_chain(task: TaskType) -> list[Callable[[], BaseChatModel | None]]:
    """Build the provider chain for a task using the current _cloud_order."""
    with _lock:
        cloud_order = tuple(_cloud_order)
    cloud = [_CLOUD_FACTORIES[provider] for provider in cloud_order]

    def ollama_reasoning() -> BaseChatModel | None:
        return _ollama(_eff("ollama_reasoning_model", settings.ollama_reasoning_model))

    def ollama_code() -> BaseChatModel | None:
        return _ollama(_eff("ollama_code_model", settings.ollama_code_model))

    if task == "code":
        return [ollama_code, *cloud]
    return [*cloud, ollama_reasoning]


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

    for factory in _get_task_chain(task):
        llm = factory()
        if llm is not None:
            logger.debug("LLM resolved for task=%s: %s", task, type(llm).__name__)
            return llm

    logger.warning("No LLM available for task=%s — deterministic fallback active", task)
    return None


def get_llm_candidates(
    task: TaskType = "general",
    *,
    prefer_ollama: bool = False,
) -> list[BaseChatModel]:
    """Return every configured AI candidate in execution order.

    Agents that use this function can retry another model after an invocation
    failure instead of jumping directly to deterministic templates.
    """
    factories = _get_task_chain(task)
    if prefer_ollama and task != "code":
        factories = [factories[-1], *factories[:-1]]

    candidates: list[BaseChatModel] = []
    if _override_provider:
        override: BaseChatModel | None = None
        if _override_provider == "groq":
            override = _groq()
        elif _override_provider == "openai":
            override = _openai()
        elif _override_provider == "gemini":
            override = _gemini()
        elif _override_provider == "ollama":
            model = (
                _eff("ollama_code_model", settings.ollama_code_model)
                if task == "code"
                else _eff("ollama_reasoning_model", settings.ollama_reasoning_model)
            )
            override = _ollama(model)
        if override is not None:
            candidates.append(override)

    for factory in factories:
        candidate = factory()
        if candidate is None:
            continue
        candidate_model = (
            getattr(candidate, "model", None)
            or getattr(candidate, "model_name", None)
        )
        duplicate = any(
            existing is candidate
            or (
                candidate_model is not None
                and type(existing) is type(candidate)
                and (
                    getattr(existing, "model", None)
                    or getattr(existing, "model_name", None)
                ) == candidate_model
            )
            for existing in candidates
        )
        if not duplicate:
            candidates.append(candidate)
    return candidates


# ── Config state helpers (used by /config/llm endpoint) ──────────────────────

def get_config_state() -> dict:
    """Snapshot of the current LLM configuration — no LLM instances created."""
    with _lock:
        override_provider = _override_provider
        cloud_order = list(_cloud_order)
        model_overrides = dict(_model_overrides)

    has_groq = bool(settings.groq_api_key)
    has_openai = bool(settings.openai_api_key)
    has_gemini = bool(settings.gemini_api_key)

    availability = {"groq": has_groq, "openai": has_openai, "gemini": has_gemini, "ollama": True}

    def resolve(chain: list[str]) -> str:
        if override_provider:
            return override_provider
        for name in chain:
            if availability.get(name, False):
                return name
        return "none"

    def effective(key: str, default: str) -> str:
        return model_overrides.get(key, default)

    cloud = cloud_order
    return {
        "override_provider": override_provider,
        "cloud_order": cloud_order,
        "ollama_base_url": settings.ollama_base_url,
        "providers": [
            {
                "name": "groq",
                "has_key": has_groq,
                "model": effective("groq_model", settings.groq_model),
                "default_model": settings.groq_model,
            },
            {
                "name": "openai",
                "has_key": has_openai,
                "model": effective("openai_model", settings.openai_model),
                "default_model": settings.openai_model,
            },
            {
                "name": "gemini",
                "has_key": has_gemini,
                "model": effective("gemini_model", settings.gemini_model),
                "default_model": settings.gemini_model,
            },
            {
                "name": "ollama",
                "has_key": True,
                "model": effective("ollama_reasoning_model", settings.ollama_reasoning_model),
                "default_model": settings.ollama_reasoning_model,
                "code_model": effective("ollama_code_model", settings.ollama_code_model),
                "default_code_model": settings.ollama_code_model,
            },
        ],
        "task_routing": {
            "technology": resolve(["ollama"] + cloud),
            "reasoning": resolve(cloud + ["ollama"]),
            "code": resolve(["ollama"] + cloud),
            "spec": resolve(cloud + ["ollama"]),
            "general": resolve(cloud + ["ollama"]),
        },
    }


def apply_config_update(update: object) -> None:
    """Thread-safe apply of a LLMConfigUpdate payload to the runtime state."""
    global _override_provider, _model_overrides, _cloud_order

    with _lock:
        if "override_provider" in getattr(update, "model_fields_set", set()):
            _override_provider = update.override_provider  # type: ignore[attr-defined]

        new_order = getattr(update, "cloud_order", None)
        if new_order is not None:
            _cloud_order = list(new_order)

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
