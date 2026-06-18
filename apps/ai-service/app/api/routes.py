from fastapi import APIRouter

from app.agents.openspec_agent import OpenSpecAgent
from app.agents.product_agent import ProductAgent
from app.agents.requirements_agent import RequirementsAgent
from app.schemas.idea import IdeaRequest
from app.schemas.openspec import OpenSpecResponse
from app.schemas.requirements import RequirementsResponse

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "progresia-ai-service",
    }


@router.post("/analyze-idea")
def analyze_idea(payload: IdeaRequest) -> dict[str, object]:
    return ProductAgent().analyze(payload)


@router.post("/generate-requirements", response_model=RequirementsResponse)
def generate_requirements(payload: IdeaRequest) -> RequirementsResponse:
    return RequirementsAgent().generate(payload)


@router.post("/generate-openspec", response_model=OpenSpecResponse)
def generate_openspec(payload: IdeaRequest) -> OpenSpecResponse:
    requirements = RequirementsAgent().generate(payload)
    return OpenSpecAgent().generate(payload, requirements)
