from fastapi import FastAPI

from app.api.routes import router
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title="ProgresIA Studio AI Service",
    description="Servicio para agentes, RAG y generación de especificaciones.",
    version="0.1.0",
)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "ready",
    }
