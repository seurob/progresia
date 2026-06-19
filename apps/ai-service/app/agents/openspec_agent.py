"""OpenSpecAgent: transforms an idea + requirements into the canonical OpenSpec document.

The OpenSpec is the single source of truth for everything downstream:
  - IssueGeneratorAgent reads spec.requirements, spec.user_stories, spec.architecture
  - CodeGenerationAgent reads spec.architecture.type to dispatch the right template
  - TutorialAgent reads spec.architecture.stack to generate setup commands

Output structure is always OpenSpecDoc — typed, canonical, no key guessing.
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.core.llm import TaskType, get_llm
from app.schemas.idea import IdeaRequest
from app.schemas.openspec import (
    OpenSpecArchitecture,
    OpenSpecConstraints,
    OpenSpecDoc,
    OpenSpecModule,
    OpenSpecProject,
    OpenSpecRequirement,
    OpenSpecResponse,
    OpenSpecUserStory,
)
from app.schemas.requirements import RequirementsResponse

logger = logging.getLogger(__name__)

# ── Architecture metadata lookup ───────────────────────────────────────────────
# Maps architecture_type → (display name, representative stack, difficulty)
_ARCH_META: dict[str, tuple[str, list[str], str]] = {
    "LARAVEL_MONOLITH":      ("Laravel 11 Monolítico (REST API)",          ["Laravel 11", "PostgreSQL 16", "Laravel Sanctum", "Docker", "nginx"],                         "BEGINNER"),
    "LARAVEL_INERTIA_REACT": ("Laravel 11 + Inertia + React",              ["Laravel 11", "Inertia.js 2", "React 19", "Vite 6", "PostgreSQL 16"],                          "INTERMEDIATE"),
    "LARAVEL_INERTIA_VUE":   ("Laravel 11 + Inertia + Vue",                ["Laravel 11", "Inertia.js 2", "Vue 3", "Vite 6", "PostgreSQL 16"],                             "INTERMEDIATE"),
    "NEXTJS_APP":            ("Next.js 15 Full-stack (App Router)",         ["Next.js 15", "TypeScript 5", "Prisma 6", "PostgreSQL 16", "Tailwind CSS 4", "NextAuth 5"],    "INTERMEDIATE"),
    "NESTJS_REACT":          ("NestJS + React (Fullstack desacoplado)",     ["NestJS 11", "React 19", "TypeScript 5", "Prisma 6", "PostgreSQL 16", "Docker"],               "INTERMEDIATE"),
    "FASTAPI_AI":            ("FastAPI + Microservicio IA (RAG + Agentes)", ["FastAPI 0.115", "LangChain 0.3", "LangGraph 0.5", "Qdrant 1", "PostgreSQL 16"],              "ADVANCED"),
    "DJANGO_REST":           ("Django 5 + Django REST Framework",           ["Django 5", "DRF 3", "simplejwt 5", "PostgreSQL 16", "psycopg2 2", "Docker"],                 "BEGINNER"),
    "REACT_EXPRESS":         ("React + Express (Node.js sencillo)",         ["React 19", "Express 5", "TypeScript 5", "Prisma 6", "PostgreSQL 16"],                        "BEGINNER"),
}

_DEFAULT_MILESTONES = [
    "Milestone 1: Setup y arquitectura",
    "Milestone 2: Modelos y base de datos",
    "Milestone 3: API y lógica de negocio",
    "Milestone 4: Frontend y UX",
    "Milestone 5: Testing y despliegue",
]

# ── LLM output model ────────────────────────────────────────────────────────────

class _RequirementLLM(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class _UserStoryLLM(BaseModel):
    id: str
    actor: str
    goal: str
    benefit: str


class _OpenSpecLLMOutput(BaseModel):
    """Structured output the LLM must return — maps directly to OpenSpecDoc."""
    project_description: str                                                # one paragraph
    requirements: list[_RequirementLLM] = Field(default_factory=list)
    user_stories: list[_UserStoryLLM]   = Field(default_factory=list)
    modules: list[str]                  = Field(default_factory=list)
    milestones: list[str]               = Field(default_factory=list)
    delivery: str = "MVP dockerizado y documentado"
    environments: list[str] = Field(default_factory=lambda: ["desarrollo", "producción"])


# ── Prompts ─────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Eres un arquitecto de software generando la especificación OpenSpec de un proyecto MVP.

A partir de la idea del proyecto y sus requisitos, genera un documento OpenSpec estructurado.
Responde SIEMPRE en español, independientemente del idioma de la entrada.

Debes devolver un JSON con este esquema exacto:
{
  "project_description": "Párrafo de 2-3 frases describiendo el proyecto, qué problema resuelve y para quién.",
  "requirements": [
    {
      "id": "RF-001",
      "title": "Título corto del requisito",
      "description": "Descripción técnica de lo que el sistema debe hacer.",
      "acceptance_criteria": [
        "El sistema debe permitir...",
        "El endpoint devuelve...",
        "La validación rechaza..."
      ]
    }
  ],
  "user_stories": [
    {
      "id": "US-001",
      "actor": "Tipo de usuario (Administrador, Cliente, etc.)",
      "goal": "acción concreta que quiere realizar",
      "benefit": "beneficio que obtiene al lograrlo"
    }
  ],
  "modules": ["Auth", "NombreModulo1", "NombreModulo2"],
  "milestones": [
    "Milestone 1: Setup y arquitectura",
    "Milestone 2: Modelos y base de datos",
    "Milestone 3: API y lógica de negocio",
    "Milestone 4: Frontend y UX",
    "Milestone 5: Testing y despliegue"
  ],
  "delivery": "Descripción breve del tipo de despliegue",
  "environments": ["desarrollo", "producción"]
}

Reglas:
- Genera TODOS los requisitos proporcionados, añadiendo criterios de aceptación específicos a cada uno
- Los criterios de aceptación deben ser verificables (endpoints, validaciones, comportamientos concretos)
- Los módulos son los bounded contexts del sistema (máx 6)
- Los milestones deben cubrir el ciclo completo del MVP
- Sé conciso pero técnicamente preciso"""


def _build_human_message(idea: IdeaRequest, requirements: RequirementsResponse) -> str:
    req_lines = "\n".join(
        f"  - {r.id}: {r.title} — {r.description}"
        for r in requirements.functional_requirements
    )
    story_lines = "\n".join(
        f"  - {s.id}: Como {s.actor}, quiero {s.goal} para {s.benefit}"
        for s in requirements.user_stories
    )
    arch_line = f"Arquitectura elegida: {idea.architecture_type}" if idea.architecture_type else "Arquitectura: a determinar"

    return f"""Proyecto: {idea.name}
Sector: {idea.sector}
Problema: {idea.problem}
Usuarios objetivo: {idea.target_users}
{arch_line}
Necesita auth: {idea.needs_auth} | Panel admin: {idea.needs_admin_panel} | IA: {idea.needs_ai}

Requisitos funcionales:
{req_lines}

Historias de usuario:
{story_lines if story_lines else "  (ninguna proporcionada)"}"""


# ── Agent ────────────────────────────────────────────────────────────────────────

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
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=_build_human_message(idea, requirements)),
                ])
                if isinstance(result, _OpenSpecLLMOutput):
                    doc = self._llm_output_to_doc(result, idea, requirements)
                    return OpenSpecResponse(
                        project_name=idea.name,
                        spec=doc.model_dump(),
                    )
            except Exception as exc:
                logger.warning("LLM openspec generation failed, using fallback: %s", exc)

        return self._deterministic_generate(idea, requirements)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _llm_output_to_doc(
        self,
        output: _OpenSpecLLMOutput,
        idea: IdeaRequest,
        requirements: RequirementsResponse,
    ) -> OpenSpecDoc:
        architecture = self._build_architecture(idea.architecture_type)
        milestones   = output.milestones if len(output.milestones) >= 3 else _DEFAULT_MILESTONES

        return OpenSpecDoc(
            project=OpenSpecProject(
                name=idea.name,
                sector=idea.sector,
                target_users=idea.target_users,
                problem=idea.problem,
                description=output.project_description,
            ),
            architecture=architecture,
            requirements=[
                OpenSpecRequirement(
                    id=r.id,
                    title=r.title,
                    description=r.description,
                    acceptance_criteria=r.acceptance_criteria,
                )
                for r in output.requirements
            ] or self._map_requirements(requirements),
            user_stories=[
                OpenSpecUserStory(id=s.id, actor=s.actor, goal=s.goal, benefit=s.benefit)
                for s in output.user_stories
            ] or self._map_user_stories(requirements),
            modules=output.modules or [m for m in ["Auth", idea.name.split()[0]] if m],
            milestones=milestones,
            constraints=OpenSpecConstraints(
                delivery=output.delivery,
                environments=output.environments,
            ),
        )

    def _deterministic_generate(
        self,
        idea: IdeaRequest,
        requirements: RequirementsResponse,
    ) -> OpenSpecResponse:
        architecture = self._build_architecture(idea.architecture_type)

        doc = OpenSpecDoc(
            project=OpenSpecProject(
                name=idea.name,
                sector=idea.sector,
                target_users=idea.target_users,
                problem=idea.problem,
                description=(
                    f"{idea.name} es una aplicación para el sector {idea.sector} "
                    f"que resuelve: {idea.problem}. "
                    f"Dirigida a: {idea.target_users}."
                ),
            ),
            architecture=architecture,
            requirements=self._map_requirements(requirements),
            user_stories=self._map_user_stories(requirements),
            modules=self._infer_modules(idea, requirements),
            milestones=_DEFAULT_MILESTONES,
            constraints=OpenSpecConstraints(
                delivery="MVP dockerizado y documentado",
                environments=["desarrollo", "producción"],
            ),
        )
        return OpenSpecResponse(project_name=idea.name, spec=doc.model_dump())

    @staticmethod
    def _build_architecture(architecture_type: str | None) -> OpenSpecArchitecture:
        if not architecture_type:
            return OpenSpecArchitecture()
        meta = _ARCH_META.get(architecture_type)
        if meta is None:
            return OpenSpecArchitecture(type=architecture_type)
        name, stack, difficulty = meta
        return OpenSpecArchitecture(
            type=architecture_type,
            name=name,
            stack=stack,
            difficulty=difficulty,
        )

    @staticmethod
    def _map_requirements(requirements: RequirementsResponse) -> list[OpenSpecRequirement]:
        return [
            OpenSpecRequirement(
                id=r.id,
                title=r.title,
                description=r.description,
                acceptance_criteria=[
                    f"El sistema implementa correctamente: {r.title}",
                    "La funcionalidad está cubierta por tests",
                ],
            )
            for r in requirements.functional_requirements
        ]

    @staticmethod
    def _map_user_stories(requirements: RequirementsResponse) -> list[OpenSpecUserStory]:
        return [
            OpenSpecUserStory(id=s.id, actor=s.actor, goal=s.goal, benefit=s.benefit)
            for s in requirements.user_stories
        ]

    @staticmethod
    def _infer_modules(idea: IdeaRequest, requirements: RequirementsResponse) -> list[str]:
        modules: list[str] = []
        if idea.needs_auth:
            modules.append("Auth")
        for feature in idea.core_features[:4]:
            word = feature.split()[0].capitalize()
            if word not in modules and len(word) > 2:
                modules.append(word)
        if idea.needs_admin_panel and "Admin" not in modules:
            modules.append("Admin")
        return modules or ["Core"]
