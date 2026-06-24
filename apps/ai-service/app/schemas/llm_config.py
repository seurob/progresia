from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator

CloudProvider = Literal["groq", "openai", "gemini"]
ProviderName = Literal["groq", "openai", "gemini", "ollama"]
_CLOUD_PROVIDERS = {"groq", "openai", "gemini"}


class ProviderInfo(BaseModel):
    name: str
    has_key: bool
    model: str
    default_model: str
    code_model: str | None = None
    default_code_model: str | None = None


class TaskRouting(BaseModel):
    reasoning: str
    code: str
    spec: str
    general: str


class LLMConfigResponse(BaseModel):
    override_provider: str | None
    providers: list[ProviderInfo]
    task_routing: TaskRouting
    ollama_base_url: str
    cloud_order: list[str]


class LLMConfigUpdate(BaseModel):
    override_provider: ProviderName | None = None
    groq_model: str | None = None
    openai_model: str | None = None
    gemini_model: str | None = None
    ollama_reasoning_model: str | None = None
    ollama_code_model: str | None = None
    cloud_order: list[CloudProvider] | None = None
    reset_models: bool = False

    @field_validator("cloud_order")
    @classmethod
    def validate_cloud_order(
        cls,
        providers: list[CloudProvider] | None,
    ) -> list[CloudProvider] | None:
        if providers is None:
            return None
        if len(providers) != len(set(providers)):
            raise ValueError("cloud_order cannot contain duplicate providers")
        if set(providers) != _CLOUD_PROVIDERS:
            raise ValueError("cloud_order must contain groq, openai and gemini exactly once")
        return providers

    @field_validator(
        "groq_model",
        "openai_model",
        "gemini_model",
        "ollama_reasoning_model",
        "ollama_code_model",
    )
    @classmethod
    def normalize_model_name(cls, model: str | None) -> str | None:
        if model is None:
            return None
        normalized = model.strip()
        if not normalized:
            raise ValueError("model names cannot be blank")
        return normalized


class OllamaModel(BaseModel):
    name: str
    size: int | None = None
    modified_at: str | None = None
    parameter_size: str | None = None
    quantization_level: str | None = None


class OllamaModelsResponse(BaseModel):
    available: bool
    base_url: str
    models: list[OllamaModel]
    error: str | None = None
