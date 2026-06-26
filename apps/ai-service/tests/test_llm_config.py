from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core import llm
from app.schemas.llm_config import LLMConfigUpdate
from app.services.model_catalog_service import ModelCatalogService


def test_cloud_order_requires_each_provider_once() -> None:
    update = LLMConfigUpdate(cloud_order=["gemini", "groq", "openai"])
    assert update.cloud_order == ["gemini", "groq", "openai"]

    with pytest.raises(ValidationError):
        LLMConfigUpdate(cloud_order=["groq", "groq", "openai"])


def test_model_names_are_trimmed_and_cannot_be_blank() -> None:
    update = LLMConfigUpdate(openai_model="  gpt-test  ")
    assert update.openai_model == "gpt-test"

    with pytest.raises(ValidationError):
        LLMConfigUpdate(openai_model="   ")


def test_apply_config_update_changes_routing_order() -> None:
    original_order = list(llm._cloud_order)
    original_override = llm._override_provider
    try:
        llm.apply_config_update(
            LLMConfigUpdate(
                override_provider=None,
                cloud_order=["gemini", "openai", "groq"],
            )
        )
        state = llm.get_config_state()
        assert state["cloud_order"] == ["gemini", "openai", "groq"]
    finally:
        llm._cloud_order = original_order
        llm._override_provider = original_override


def test_ai_candidates_can_prioritize_local_ollama() -> None:
    ollama_model = object()
    groq_model = object()
    with (
        patch("app.core.llm._ollama", return_value=ollama_model),
        patch.dict(
            "app.core.llm._CLOUD_FACTORIES",
            {
                "groq": lambda: groq_model,
                "openai": lambda: None,
                "gemini": lambda: None,
            },
        ),
    ):
        candidates = llm.get_llm_candidates("reasoning", prefer_ollama=True)

    assert candidates == [ollama_model, groq_model]


def test_ollama_disables_reasoning_output_for_chat_models() -> None:
    captured: dict[str, object] = {}

    def fake_chat_ollama(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    with patch("langchain_ollama.ChatOllama", side_effect=fake_chat_ollama):
        model = llm._ollama("gemma4:26b-a4b-it-qat")

    assert model is not None
    assert captured["model"] == "gemma4:26b-a4b-it-qat"
    assert captured["reasoning"] is False


def test_model_catalog_filters_openai_chat_models() -> None:
    def fetch_json(url: str, headers: dict[str, str], timeout: float) -> dict:
        assert url == "https://api.openai.com/v1/models"
        assert headers["Authorization"] == "Bearer test-key"
        assert timeout == 5
        return {
            "data": [
                {"id": "gpt-4.1-mini"},
                {"id": "o3-mini"},
                {"id": "text-embedding-3-small"},
            ]
        }

    with (
        patch("app.services.model_catalog_service.settings.groq_api_key", ""),
        patch("app.services.model_catalog_service.settings.openai_api_key", "test-key"),
        patch("app.services.model_catalog_service.settings.gemini_api_key", ""),
    ):
        catalogs = ModelCatalogService(fetch_json).list_cloud_models()

    assert catalogs == {"openai": ["gpt-4.1-mini", "o3-mini"]}


def test_model_catalog_returns_configured_fallback_on_provider_error() -> None:
    def failing_fetch(url: str, headers: dict[str, str], timeout: float) -> dict:
        raise TimeoutError

    with (
        patch("app.services.model_catalog_service.settings.groq_api_key", "test-key"),
        patch("app.services.model_catalog_service.settings.groq_model", "fallback-model"),
        patch("app.services.model_catalog_service.settings.openai_api_key", ""),
        patch("app.services.model_catalog_service.settings.gemini_api_key", ""),
    ):
        catalogs = ModelCatalogService(failing_fetch).list_cloud_models()

    assert catalogs == {"groq": ["fallback-model"]}


def test_ollama_failure_returns_safe_error_without_exception_details() -> None:
    def failing_fetch(url: str, headers: dict[str, str], timeout: float) -> dict:
        raise RuntimeError("sensitive internal detail")

    with patch(
        "app.services.model_catalog_service.settings.ollama_base_url",
        "http://localhost:11434/",
    ):
        response = ModelCatalogService(failing_fetch).list_ollama_models()

    assert response.available is False
    assert response.base_url == "http://localhost:11434"
    assert response.error == "Ollama is not reachable"
