import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import TaskType, get_llm
from app.schemas.idea import IdeaRequest
from app.schemas.requirements import RequirementItem, RequirementsResponse, UserStory

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a product requirements analyst for software MVPs.

Given a business idea, generate a structured requirements document with:
1. Functional requirements (RF-001, RF-002, ...): specific, testable features the system must implement.
   Generate one requirement per core feature, plus any implied requirements (auth, admin if requested).
2. Non-functional requirements (RNF-001, RNF-002, ...): security, performance, reliability, deployment.
3. User stories (US-001, US-002, ...): written as "As a [actor], I want to [goal] so that [benefit]".

Be specific, actionable, and use the exact IDs format shown above.
Respond in the same language as the project name and sector."""


def _build_human_message(idea: IdeaRequest) -> str:
    features = "\n".join(f"  - {f}" for f in idea.core_features)
    return f"""Project: {idea.name}
Sector: {idea.sector}
Problem: {idea.problem}
Target users: {idea.target_users}
Core features:
{features}
Needs authentication: {idea.needs_auth}
Needs admin panel: {idea.needs_admin_panel}
Needs AI capabilities: {idea.needs_ai}"""


class RequirementsAgent:
    def generate(
        self,
        idea: IdeaRequest,
        llm: BaseChatModel | None = None,
        task: TaskType = "reasoning",
    ) -> RequirementsResponse:
        resolved_llm = llm if llm is not None else get_llm(task)

        if resolved_llm is not None:
            try:
                structured = resolved_llm.with_structured_output(RequirementsResponse)
                result = structured.invoke([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=_build_human_message(idea)),
                ])
                if isinstance(result, RequirementsResponse):
                    return result
            except Exception as exc:
                logger.warning("LLM requirements generation failed, using fallback: %s", exc)

        return self._deterministic_generate(idea)

    def _deterministic_generate(self, idea: IdeaRequest) -> RequirementsResponse:
        functional = [
            RequirementItem(
                id=f"RF-{i + 1:03}",
                title=feature,
                description=f"El sistema debe permitir gestionar: {feature}.",
            )
            for i, feature in enumerate(idea.core_features)
        ]

        if idea.needs_auth:
            functional.append(RequirementItem(
                id=f"RF-{len(functional) + 1:03}",
                title="Autenticación de usuarios",
                description="El sistema debe implementar registro, login y cierre de sesión con JWT.",
            ))

        if idea.needs_admin_panel:
            functional.append(RequirementItem(
                id=f"RF-{len(functional) + 1:03}",
                title="Panel de administración",
                description="El sistema debe incluir un panel para gestionar recursos y usuarios.",
            ))

        stories = [
            UserStory(
                id=f"US-{i + 1:03}",
                actor="Usuario principal",
                goal=feature,
                benefit="validar la propuesta de valor del MVP",
            )
            for i, feature in enumerate(idea.core_features)
        ]

        return RequirementsResponse(
            project_name=idea.name,
            functional_requirements=functional,
            non_functional_requirements=[
                RequirementItem(
                    id="RNF-001",
                    title="Seguridad básica",
                    description="La plataforma debe proteger rutas privadas y validar entradas.",
                ),
                RequirementItem(
                    id="RNF-002",
                    title="Despliegue reproducible",
                    description="El MVP debe poder levantarse localmente con Docker Compose.",
                ),
            ],
            user_stories=stories,
        )
