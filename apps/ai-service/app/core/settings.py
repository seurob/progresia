from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ProgresIA Studio AI Service"

    # Default provider used when no task-specific override is set.
    # Values: groq | openai | gemini | ollama
    llm_provider: str = "groq"

    # Groq — fast inference, best for reasoning / requirements analysis
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenAI — complex structured specs
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Google Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    # Ollama — local, no API key. The 26B-A4B profile is the balanced default;
    # users with a strong GPU or abundant RAM can switch both values to gemma4:31b.
    ollama_base_url: str = "http://localhost:11434"
    ollama_reasoning_model: str = "gemma4:26b-a4b-it-qat"
    ollama_code_model: str = "gemma4:26b-a4b-it-qat"

    qdrant_url: str = "http://localhost:6333"

    ai_sentry_dsn: str | None = None
    ai_sentry_environment: str = "development"
    ai_sentry_release: str | None = None
    ai_sentry_traces_sample_rate: float = 0.1
    ai_sentry_enable_logs: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
