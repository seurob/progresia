"""LLM configuration endpoints: read/update provider settings and browse
available models from cloud providers (via ModelCatalogService) and Ollama."""
from __future__ import annotations

from fastapi import APIRouter

from app.core.llm import apply_config_update, get_config_state
from app.schemas.llm_config import LLMConfigResponse, LLMConfigUpdate, OllamaModelsResponse
from app.services.model_catalog_service import ModelCatalogService

router = APIRouter(prefix="/config/llm")

_catalog = ModelCatalogService()


@router.get("", response_model=LLMConfigResponse)
def get_llm_config() -> LLMConfigResponse:
    """Return the current LLM provider configuration and task routing."""
    return LLMConfigResponse(**get_config_state())


@router.patch("", response_model=LLMConfigResponse)
def update_llm_config(payload: LLMConfigUpdate) -> LLMConfigResponse:
    """Override the active LLM provider and/or individual model names at runtime.

    Changes take effect immediately for all subsequent agent calls.
    They reset when the process restarts (use .env for persistent config).
    """
    apply_config_update(payload)
    return LLMConfigResponse(**get_config_state())


@router.get("/provider-models")
def list_provider_models() -> dict[str, list[str]]:
    """Fetch available chat models from each configured provider's API."""
    return _catalog.list_cloud_models()


# Ollama is grouped here because it shares the same admin concern as LLM config.
ollama_router = APIRouter(prefix="/ollama")


@ollama_router.get("/models", response_model=OllamaModelsResponse)
def list_ollama_models() -> OllamaModelsResponse:
    """List models available in the local Ollama instance."""
    return _catalog.list_ollama_models()
