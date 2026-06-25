"""Endpoints that trigger AI agent pipelines: requirements, architecture,
openspec, issues, tutorial, code, tech proposals, and feature suggestions."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from app.agents.architecture_agent import ArchitectureAgent
from app.agents.codegen_agent import CodeGenerationAgent
from app.agents.issue_generator_agent import IssueGeneratorAgent
from app.agents.product_agent import ProductAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.tech_proposal_agent import TechProposalAgent
from app.agents.tutorial_agent import TutorialAgent
from app.core.llm import get_llm
from app.schemas.architecture import ArchitectureRecommendation, ArchitectureRequest
from app.schemas.codegen import CodeGenerationRequest, CodeGenerationResponse
from app.schemas.idea import IdeaRequest
from app.schemas.issues import IssueGenerationRequest, IssueGenerationResponse
from app.schemas.openspec import OpenSpecResponse
from app.schemas.requirements import RequirementsResponse
from app.schemas.suggestion import (
    DEFAULT_FEATURES,
    SECTOR_FALLBACK,
    FeatureSuggestionRequest,
    FeatureSuggestionResponse,
)
from app.schemas.tech_proposal import TechProposalRequest, TechProposalResponse
from app.schemas.tutorial import TutorialRequest, TutorialResponse

logger = logging.getLogger(__name__)

router = APIRouter()


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
            detail="La idea necesita al menos una funcionalidad para generar el OpenSpec.",
        )

    if result["openspec"] is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El agente supervisor no pudo generar el OpenSpec.",
        )

    return result["openspec"]


@router.post("/propose-tech")
def propose_tech(payload: TechProposalRequest) -> TechProposalResponse:
    """Return 3 tech stack proposals for the given project context.

    Synchronous — no job queue needed; fast catalog fallback guarantees <200ms.
    """
    return TechProposalAgent().propose(payload)


@router.post("/generate-code")
def generate_code(payload: CodeGenerationRequest) -> CodeGenerationResponse:
    return CodeGenerationAgent().generate(payload)


@router.post("/suggest-features")
def suggest_features(payload: FeatureSuggestionRequest) -> FeatureSuggestionResponse:
    """Use LLM to suggest relevant features; falls back to curated sector lists."""
    llm = get_llm("general")
    if llm is not None:
        prompt = (
            f"Eres experto en producto digital. Sugiere exactamente 10 funcionalidades específicas para:\n"
            f"Sector: {payload.sector}\n"
            f"Problema: {payload.problem}\n"
            f"Usuarios: {payload.target_users}\n\n"
            "Responde ÚNICAMENTE con un JSON array de strings, sin texto adicional.\n"
            "Las funcionalidades deben ser concretas, en español, orientadas al usuario final.\n"
            'Ejemplo: ["Reserva online de citas","Sistema de pagos integrado",...]'
        )
        try:
            import json
            resp = llm.invoke(prompt)
            content = resp.content if hasattr(resp, "content") else str(resp)
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end > start:
                features = json.loads(content[start : end + 1])
                if isinstance(features, list) and features:
                    return FeatureSuggestionResponse(features=[str(f) for f in features[:10]])
        except Exception as exc:
            logger.warning("Feature suggestion LLM call failed: %s", exc)

    fallback = SECTOR_FALLBACK.get(payload.sector, DEFAULT_FEATURES)
    return FeatureSuggestionResponse(features=fallback)


@router.post("/recommend-architecture")
def recommend_architecture(payload: ArchitectureRequest) -> ArchitectureRecommendation:
    """Analyzes the project idea and recommends the most suitable architecture."""
    return ArchitectureAgent().recommend(payload)


@router.post("/generate-issues")
def generate_issues(payload: IssueGenerationRequest) -> IssueGenerationResponse:
    """Transforms an OpenSpec into structured GitHub Issues with milestones and labels."""
    return IssueGeneratorAgent().generate(payload)


@router.post("/generate-tutorial")
def generate_tutorial(payload: TutorialRequest) -> TutorialResponse:
    """Generates a step-by-step implementation tutorial from an OpenSpec and architecture type."""
    return TutorialAgent().generate(payload)
