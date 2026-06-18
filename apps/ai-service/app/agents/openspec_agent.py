import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from app.core.llm import TaskType, get_llm
from app.schemas.idea import IdeaRequest
from app.schemas.openspec import OpenSpecResponse
from app.schemas.requirements import RequirementsResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a software architect generating an OpenSpec document for a software MVP.

Given a business idea and its requirements, produce a structured OpenSpec with:
- project: name, sector, targetUsers, description (one paragraph)
- requirements: list of {id, title, description} mapped from the provided requirements
- constraints: stack (list of technologies) and delivery (deployment approach)
- modules: list of bounded context names (e.g. Auth, Projects, Dashboard)

Be concise and technical. Use the same language as the project name."""


class _OpenSpecLLMOutput(BaseModel):
    """Intermediate model for structured LLM output before converting to OpenSpecResponse."""
    project: dict[str, str]
    requirements: list[dict[str, str]]
    constraints: dict[str, Any]
    modules: list[str] = []


def _build_human_message(idea: IdeaRequest, requirements: RequirementsResponse) -> str:
    req_lines = "\n".join(
        f"  - {r.id}: {r.title} — {r.description}"
        for r in requirements.functional_requirements
    )
    return f"""Project: {idea.name}
Sector: {idea.sector}
Problem: {idea.problem}
Target users: {idea.target_users}
Needs auth: {idea.needs_auth} | Needs admin: {idea.needs_admin_panel} | Needs AI: {idea.needs_ai}

Functional requirements:
{req_lines}"""


class OpenSpecAgent:
    def generate(
        self,
        idea: IdeaRequest,
        requirements: RequirementsResponse,
        llm: BaseChatModel | None = None,
        task: TaskType = "spec",
    ) -> OpenSpecResponse:
        resolved_llm = llm if llm is not None else get_llm(task)

        if resolved_llm is not None:
            try:
                structured = resolved_llm.with_structured_output(_OpenSpecLLMOutput)
                result = structured.invoke([
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=_build_human_message(idea, requirements)),
                ])
                if isinstance(result, _OpenSpecLLMOutput):
                    return OpenSpecResponse(
                        project_name=idea.name,
                        spec=result.model_dump(),
                    )
            except Exception as exc:
                logger.warning("LLM openspec generation failed, using fallback: %s", exc)

        return self._deterministic_generate(idea, requirements)

    def _deterministic_generate(
        self,
        idea: IdeaRequest,
        requirements: RequirementsResponse,
    ) -> OpenSpecResponse:
        spec = {
            "project": {
                "name": idea.name,
                "sector": idea.sector,
                "targetUsers": idea.target_users,
            },
            "requirements": [
                requirement.model_dump()
                for requirement in requirements.functional_requirements
            ],
            "constraints": {
                "stack": ["React", "NestJS", "PostgreSQL", "FastAPI", "Docker"],
                "delivery": "MVP desplegable y documentado",
            },
            "modules": [],
        }
        return OpenSpecResponse(project_name=idea.name, spec=spec)
