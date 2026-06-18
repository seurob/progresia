from fastapi import APIRouter, HTTPException, status

from app.agents.codegen_agent import CodeGenerationAgent
from app.agents.product_agent import ProductAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse
from app.schemas.idea import IdeaRequest
from app.schemas.openspec import OpenSpecResponse
from app.schemas.requirements import RequirementsResponse

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "progresia-ai-service"}


@router.post("/analyze-idea")
def analyze_idea(payload: IdeaRequest) -> dict[str, object]:
    return ProductAgent().analyze(payload)


@router.post("/generate-requirements")
def generate_requirements(payload: IdeaRequest) -> RequirementsResponse:
    return RequirementsAgent().generate(payload)


@router.post("/generate-openspec")
def generate_openspec(payload: IdeaRequest) -> OpenSpecResponse:
    result = SupervisorAgent().run(payload)

    if result["decision"] == "ask_more_questions":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La idea necesita al menos 2 funcionalidades para generar el OpenSpec.",
        )

    if result["openspec"] is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El agente supervisor no pudo generar el OpenSpec.",
        )

    return result["openspec"]


@router.post("/generate-code")
def generate_code(payload: CodeGenerationRequest) -> CodeGenerationResponse:
    return CodeGenerationAgent().generate(payload)
