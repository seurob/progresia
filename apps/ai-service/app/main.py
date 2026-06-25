from fastapi import FastAPI

from app.api import llm_config, rag, specifications
from app.core.settings import settings

app = FastAPI(
    title="ProgresIA Studio AI Service",
    description="Servicio para agentes, RAG y generación de especificaciones.",
    version="0.1.0",
)

app.include_router(specifications.router)
app.include_router(llm_config.router)
app.include_router(llm_config.ollama_router)
app.include_router(rag.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ready",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "progresia-ai-service"}
