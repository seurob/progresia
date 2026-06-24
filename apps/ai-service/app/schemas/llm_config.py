from __future__ import annotations

from pydantic import BaseModel


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


class LLMConfigUpdate(BaseModel):
    override_provider: str | None = None
    groq_model: str | None = None
    openai_model: str | None = None
    gemini_model: str | None = None
    ollama_reasoning_model: str | None = None
    ollama_code_model: str | None = None
    reset_models: bool = False


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
