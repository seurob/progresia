from __future__ import annotations

import json
import logging
import urllib.request
from collections.abc import Callable
from typing import Any

from app.core.settings import settings
from app.schemas.llm_config import OllamaModel, OllamaModelsResponse

logger = logging.getLogger(__name__)

JsonFetcher = Callable[[str, dict[str, str], float], dict[str, Any]]

_NON_CHAT_MODEL_MARKERS = (
    "audio",
    "embedding",
    "image",
    "moderation",
    "prompt-guard",
    "realtime",
    "safeguard",
    "search",
    "transcribe",
    "tts",
    "whisper",
)


def _fetch_json(url: str, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode())


class ModelCatalogService:
    """Reads provider model catalogs without exposing credentials to API routes."""

    def __init__(self, fetch_json: JsonFetcher = _fetch_json) -> None:
        self._fetch_json = fetch_json

    def list_cloud_models(self) -> dict[str, list[str]]:
        catalogs: dict[str, list[str]] = {}

        if settings.groq_api_key:
            catalogs["groq"] = self._safe_catalog(
                provider="groq",
                fallback=settings.groq_model,
                loader=lambda: self._load_openai_compatible(
                    "https://api.groq.com/openai/v1/models",
                    settings.groq_api_key,
                    chat_only=True,
                ),
            )

        if settings.openai_api_key:
            catalogs["openai"] = self._safe_catalog(
                provider="openai",
                fallback=settings.openai_model,
                loader=self._load_openai,
            )

        if settings.gemini_api_key:
            catalogs["gemini"] = self._safe_catalog(
                provider="gemini",
                fallback=settings.gemini_model,
                loader=self._load_gemini,
            )

        return catalogs

    def list_ollama_models(self) -> OllamaModelsResponse:
        base_url = settings.ollama_base_url.rstrip("/")
        try:
            data = self._fetch_json(
                f"{base_url}/api/tags",
                {"Accept": "application/json"},
                3,
            )
            models = [
                OllamaModel(
                    name=model["name"],
                    size=model.get("size"),
                    modified_at=model.get("modified_at"),
                    parameter_size=model.get("details", {}).get("parameter_size"),
                    quantization_level=model.get("details", {}).get("quantization_level"),
                )
                for model in data.get("models", [])
                if model.get("name")
            ]
            return OllamaModelsResponse(available=True, base_url=base_url, models=models)
        except Exception:
            logger.debug("Ollama model catalog is unavailable")
            return OllamaModelsResponse(
                available=False,
                base_url=base_url,
                models=[],
                error="Ollama is not reachable",
            )

    def _safe_catalog(
        self,
        provider: str,
        fallback: str,
        loader: Callable[[], list[str]],
    ) -> list[str]:
        try:
            models = loader()
            return models or [fallback]
        except Exception:
            logger.debug("%s model catalog is unavailable", provider)
            return [fallback]

    def _load_openai_compatible(
        self,
        url: str,
        api_key: str,
        *,
        chat_only: bool = False,
    ) -> list[str]:
        data = self._fetch_json(
            url,
            {"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            5,
        )
        models = [model["id"] for model in data.get("data", []) if model.get("id")]
        if chat_only:
            models = [model for model in models if self._is_chat_model(model)]
        return sorted(models)

    def _load_openai(self) -> list[str]:
        models = self._load_openai_compatible(
            "https://api.openai.com/v1/models",
            settings.openai_api_key,
            chat_only=True,
        )
        accepted_markers = ("gpt-", "o1", "o3", "o4")
        return [model for model in models if model.startswith(accepted_markers)]

    @staticmethod
    def _is_chat_model(model: str) -> bool:
        normalized = model.lower()
        return not any(marker in normalized for marker in _NON_CHAT_MODEL_MARKERS)

    def _load_gemini(self) -> list[str]:
        data = self._fetch_json(
            "https://generativelanguage.googleapis.com/v1beta/models"
            f"?key={settings.gemini_api_key}",
            {"Accept": "application/json"},
            5,
        )
        return sorted(
            model["name"].removeprefix("models/")
            for model in data.get("models", [])
            if "gemini" in model.get("name", "").lower()
            and "generateContent" in model.get("supportedGenerationMethods", [])
        )
