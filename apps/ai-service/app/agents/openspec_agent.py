"""OpenSpecAgent: transforms an idea + requirements into the canonical OpenSpec document.

The OpenSpec is the SINGLE SOURCE OF TRUTH for everything downstream:
  - IssueGeneratorAgent reads spec.requirements, spec.user_stories, spec.modules
  - CodeGenerationAgent reads spec.architecture.type + spec.data_entities + spec.api_endpoints
  - TutorialAgent reads spec.architecture.stack + spec.dev_steps

The richer this spec, the better the generated code and tutorials will be.
"""
from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.core.llm import TaskType, get_llm
from app.schemas.idea import IdeaRequest
from app.schemas.openspec import (
    OpenSpecApiEndpoint,
    OpenSpecArchitecture,
    OpenSpecConstraints,
    OpenSpecDataEntity,
    OpenSpecDataModel,
    OpenSpecDevStep,
    OpenSpecDoc,
    OpenSpecProject,
    OpenSpecRelationship,
    OpenSpecRequirement,
    OpenSpecResponse,
    OpenSpecUserStory,
)
from app.schemas.requirements import RequirementsResponse

logger = logging.getLogger(__name__)

# ── Architecture → DB / ORM metadata ──────────────────────────────────────────
_ORM_ELOQUENT   = "Eloquent ORM"
_ORM_PRISMA     = "Prisma 6"
_ORM_SQLMODEL   = "SQLModel"
_ORM_DJANGO     = "Django ORM"

_RATIONALE_ELOQUENT = "Incluido en Laravel; soporte nativo para migraciones, seeds y relaciones."
_RATIONALE_PRISMA   = "Prisma genera tipos TypeScript seguros y gestiona migraciones SQL con autocompletado total."

# Tech version constants reused across _ARCH_META and _ARCH_DB
_V_LARAVEL    = "Laravel 11"
_V_REACT      = "React 19"
_V_TS         = "TypeScript 5"
_V_PG         = "PostgreSQL 16"
_V_INERTIA    = "Inertia.js 2"
_V_VUE        = "Vue 3"
_V_VITE       = "Vite 6"
_V_NEXTJS     = "Next.js 15"
_V_NESTJS     = "NestJS 11"
_V_FASTAPI    = "FastAPI 0.115"
_V_DJANGO     = "Django 5"

# (technology, orm, orm_rationale)
_ARCH_DB: dict[str, tuple[str, str, str]] = {
    "LARAVEL_MONOLITH":      ("PostgreSQL",           _ORM_ELOQUENT, _RATIONALE_ELOQUENT),
    "LARAVEL_INERTIA_REACT": ("PostgreSQL",           _ORM_ELOQUENT, _RATIONALE_ELOQUENT),
    "LARAVEL_INERTIA_VUE":   ("PostgreSQL",           _ORM_ELOQUENT, _RATIONALE_ELOQUENT),
    "NEXTJS_APP":            ("PostgreSQL",           _ORM_PRISMA,   _RATIONALE_PRISMA),
    "NESTJS_REACT":          ("PostgreSQL",           _ORM_PRISMA,   _RATIONALE_PRISMA),
    "FASTAPI_AI":            ("PostgreSQL + Qdrant",  _ORM_SQLMODEL, "SQLModel combina Pydantic y SQLAlchemy para el modelo relacional; Qdrant gestiona embeddings vectoriales."),
    "DJANGO_REST":           ("PostgreSQL",           _ORM_DJANGO,   "Django ORM incorpora migraciones automáticas, admin panel y validaciones de modelo."),
    "REACT_EXPRESS":         ("PostgreSQL",           _ORM_PRISMA,   "Prisma es el ORM más completo para proyectos Node.js/TypeScript con validación de tipos en tiempo de compilación."),
}

# ── Architecture metadata lookup ────────────────────────────────────────────────
_ARCH_META: dict[str, tuple[str, list[str], str]] = {
    "LARAVEL_MONOLITH":      (f"{_V_LARAVEL} Monolítico (REST API)",          [_V_LARAVEL, _V_PG, "Laravel Sanctum", "Docker", "nginx"],                          "BEGINNER"),
    "LARAVEL_INERTIA_REACT": (f"{_V_LARAVEL} + Inertia + React",              [_V_LARAVEL, _V_INERTIA, _V_REACT, _V_VITE, _V_PG],                               "INTERMEDIATE"),
    "LARAVEL_INERTIA_VUE":   (f"{_V_LARAVEL} + Inertia + Vue",                [_V_LARAVEL, _V_INERTIA, _V_VUE, _V_VITE, _V_PG],                                  "INTERMEDIATE"),
    "NEXTJS_APP":            (f"{_V_NEXTJS} Full-stack (App Router)",          [_V_NEXTJS, _V_TS, _ORM_PRISMA, _V_PG, "Tailwind CSS 4", "NextAuth 5"],            "INTERMEDIATE"),
    "NESTJS_REACT":          (f"{_V_NESTJS} + React (Fullstack desacoplado)",  [_V_NESTJS, _V_REACT, _V_TS, _ORM_PRISMA, _V_PG, "Docker"],                       "INTERMEDIATE"),
    "FASTAPI_AI":            (f"{_V_FASTAPI} + Microservicio IA (RAG+Agents)", [_V_FASTAPI, "LangChain 0.3", "LangGraph 0.5", "Qdrant 1", _V_PG],                "ADVANCED"),
    "DJANGO_REST":           (f"{_V_DJANGO} + Django REST Framework",          [_V_DJANGO, "DRF 3", "simplejwt 5", _V_PG, "psycopg2 2", "Docker"],               "BEGINNER"),
    "REACT_EXPRESS":         ("React + Express (Node.js sencillo)",            [_V_REACT, "Express 5", _V_TS, _ORM_PRISMA, _V_PG],                               "BEGINNER"),
}

_DEFAULT_MILESTONES = [
    "Milestone 1: Setup y arquitectura base",
    "Milestone 2: Modelos y migraciones de base de datos",
    "Milestone 3: API backend y lógica de negocio",
    "Milestone 4: Frontend e interfaz de usuario",
    "Milestone 5: Testing, CI/CD y despliegue",
]

# ── LLM output model ─────────────────────────────────────────────────────────────

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


class _DataEntityLLM(BaseModel):
    name: str
    description: str = ""
    fields: list[str] = Field(default_factory=list)
    relations: list[str] = Field(default_factory=list)


class _RelationshipLLM(BaseModel):
    from_entity: str
    to_entity: str
    type: str = "one_to_many"
    through: str = ""
    cascade_delete: bool = False
    optional: bool = False
    label: str = ""


class _DataModelLLM(BaseModel):
    storage_type: str = "relational"
    technology: str = "PostgreSQL"
    justification: str = ""
    orm: str = ""
    orm_rationale: str = ""
    relationships: list[_RelationshipLLM] = Field(default_factory=list)
    indexes: list[str] = Field(default_factory=list)
    mermaid_diagram: str = ""
    seed_needed: bool = False
    seed_instructions: list[str] = Field(default_factory=list)
    security_notes: list[str] = Field(default_factory=list)
    mvp_scope: list[str] = Field(default_factory=list)
    future_scope: list[str] = Field(default_factory=list)


class _ApiEndpointLLM(BaseModel):
    method: str
    path: str
    description: str
    auth_required: bool = True
    request_body: str = ""
    response: str = ""


class _DevStepLLM(BaseModel):
    step: int
    title: str
    description: str
    commands: list[str] = Field(default_factory=list)


class _OpenSpecLLMOutput(BaseModel):
    """Structured output the LLM must return — maps 1:1 to OpenSpecDoc."""
    project_description: str
    requirements: list[_RequirementLLM]      = Field(default_factory=list)
    user_stories: list[_UserStoryLLM]        = Field(default_factory=list)
    modules: list[str]                       = Field(default_factory=list)
    milestones: list[str]                    = Field(default_factory=list)
    data_entities: list[_DataEntityLLM]      = Field(default_factory=list)
    data_model: _DataModelLLM                = Field(default_factory=_DataModelLLM)
    api_endpoints: list[_ApiEndpointLLM]     = Field(default_factory=list)
    business_rules: list[str]                = Field(default_factory=list)
    dev_steps: list[_DevStepLLM]             = Field(default_factory=list)
    delivery: str = "MVP dockerizado y documentado"
    environments: list[str] = Field(default_factory=lambda: ["desarrollo", "producción"])


# ── Prompts ───────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """Eres un arquitecto de software senior generando la especificación OpenSpec completa de un proyecto MVP.

Esta especificación será utilizada directamente por una IA para implementar el proyecto.
CUANTO MÁS DETALLADA Y PRECISA sea, mejor será el código generado.

Responde SIEMPRE en español. Devuelve un JSON con este esquema exacto:

{
  "project_description": "2-3 frases claras: qué es el sistema, qué problema resuelve, para quién.",

  "requirements": [
    {
      "id": "RF-001",
      "title": "Título corto del requisito funcional",
      "description": "Descripción técnica y precisa de lo que el sistema debe implementar.",
      "acceptance_criteria": [
        "El endpoint POST /api/recurso devuelve 201 con { id, ...campos }",
        "La validación rechaza campos vacíos con 422 y mensaje descriptivo",
        "El usuario autenticado puede ver solo sus propios recursos"
      ]
    }
  ],

  "user_stories": [
    {
      "id": "US-001",
      "actor": "Tipo de usuario (Administrador, Cliente, Profesor, etc.)",
      "goal": "acción concreta que quiere realizar en la plataforma",
      "benefit": "beneficio medible que obtiene al completar la acción"
    }
  ],

  "modules": ["Auth", "NombreModulo1", "NombreModulo2"],

  "milestones": [
    "Milestone 1: Setup y arquitectura base",
    "Milestone 2: Modelos y migraciones",
    "Milestone 3: API y lógica de negocio",
    "Milestone 4: Frontend e interfaz",
    "Milestone 5: Testing y despliegue"
  ],

  "data_entities": [
    {
      "name": "User",
      "description": "Usuario registrado en la plataforma",
      "fields": [
        "id: UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "email: VARCHAR(255) UNIQUE NOT NULL",
        "password_hash: VARCHAR(255) NOT NULL",
        "name: VARCHAR(100) NOT NULL",
        "role: ENUM('admin', 'user') DEFAULT 'user'",
        "created_at: TIMESTAMPTZ DEFAULT now()",
        "updated_at: TIMESTAMPTZ DEFAULT now()"
      ],
      "relations": ["has_many Orders", "belongs_to Organization optional"]
    }
  ],

  "api_endpoints": [
    {
      "method": "POST",
      "path": "/api/auth/register",
      "description": "Registro de nuevo usuario con validación de email único",
      "auth_required": false,
      "request_body": "{ email: string, password: string, name: string }",
      "response": "201 { access_token: string, user: { id, email, name, role } }"
    },
    {
      "method": "GET",
      "path": "/api/recursos",
      "description": "Lista paginada de recursos del usuario autenticado",
      "auth_required": true,
      "request_body": "",
      "response": "200 { data: Recurso[], total: number, page: number }"
    }
  ],

  "business_rules": [
    "Un usuario solo puede acceder a sus propios recursos (aislamiento por userId)",
    "El email debe ser único y verificado antes de permitir el acceso completo",
    "Las contraseñas deben tener mínimo 8 caracteres, una mayúscula, un número y un símbolo",
    "Los recursos en estado 'activo' no pueden eliminarse sin desactivarse primero"
  ],

  "dev_steps": [
    {
      "step": 1,
      "title": "Configurar proyecto y entorno Docker",
      "description": "Crear la estructura base del proyecto, Docker Compose con la base de datos y variables de entorno",
      "commands": [
        "git init && git commit -m 'chore: init repo'",
        "cp .env.example .env",
        "docker compose up -d postgres redis"
      ]
    },
    {
      "step": 2,
      "title": "Crear modelos y migraciones de base de datos",
      "description": "Definir los modelos del dominio y ejecutar las migraciones iniciales",
      "commands": [
        "npx prisma migrate dev --name init",
        "npx prisma generate"
      ]
    }
  ],

  "data_model": {
    "storage_type": "relational",
    "technology": "PostgreSQL",
    "justification": "Explica qué datos almacena, por qué encaja con el MVP, ventajas, limitaciones y alternativas. Indica si es adecuado para el nivel del desarrollador.",
    "orm": "Prisma 6",
    "orm_rationale": "Por qué se recomienda este ORM con el stack elegido.",
    "relationships": [
      {
        "from_entity": "User",
        "to_entity": "Task",
        "type": "one_to_many",
        "through": "",
        "cascade_delete": true,
        "optional": false,
        "label": "crea"
      }
    ],
    "indexes": [
      "CREATE UNIQUE INDEX idx_users_email ON users(email)",
      "CREATE INDEX idx_tasks_project_id ON tasks(project_id)",
      "CREATE INDEX idx_tasks_status ON tasks(project_id, status)"
    ],
    "mermaid_diagram": "erDiagram\\n    USER ||--o{ TASK : crea\\n    USER {\\n        uuid id PK\\n        string email UK\\n        string password_hash\\n        datetime created_at\\n    }\\n    TASK {\\n        uuid id PK\\n        string title\\n        string status\\n        uuid user_id FK\\n        datetime created_at\\n    }",
    "seed_needed": true,
    "seed_instructions": [
      "npm run db:seed  # crea usuarios de prueba y datos iniciales",
      "Usuario admin: admin@example.com / password seguro via .env"
    ],
    "security_notes": [
      "Contraseñas almacenadas con bcrypt (mínimo 12 rondas)",
      "Datos sensibles solo en variables de entorno, nunca en código",
      "Acceso a recursos validado por userId en cada query"
    ],
    "mvp_scope": ["User", "Task", "Category"],
    "future_scope": ["AuditLog", "Notification", "TeamMembership"]
  },

  "delivery": "MVP dockerizado con README, variables de entorno documentadas y primer despliegue en Railway/Render",
  "environments": ["desarrollo", "staging", "producción"]
}

REGLAS CRÍTICAS:
1. data_entities: Define TODOS los modelos del dominio. Fields en notación SQL precisa con tipos, constraints y defaults.
2. api_endpoints: Cubre TODOS los endpoints del MVP (mínimo 8-12). Incluye autenticación, CRUD principal y endpoints especiales.
3. business_rules: Lista las reglas de negocio más importantes — validaciones, permisos, limitaciones de uso.
4. dev_steps: 5-8 pasos ordenados lógicamente. Incluye comandos reales del stack elegido.
5. requirements: Genera TODOS los requisitos con criterios de aceptación VERIFICABLES (endpoints, validaciones, comportamientos).
6. acceptance_criteria: Usa formato técnico concreto — no "debería funcionar", sino "POST /api/X devuelve 201 con { campo }".
7. Sé específico del dominio — no genérico. Los nombres de endpoints, entidades y campos deben reflejar el negocio real.
8. data_model: genera SIEMPRE esta sección completa con justificación, ORM, relaciones con tipos precisos, índices recomendados, diagrama Mermaid ER, instrucciones de seed y notas de seguridad.
9. mermaid_diagram: diagrama ER válido con entidades, campos clave (tipos + PK/FK/UK) y relaciones. Formato: erDiagram con bloques de entidad y líneas de relación."""


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
    level_line = f"Nivel técnico del desarrollador: {idea.technical_level}"

    return f"""Proyecto: {idea.name}
Sector: {idea.sector}
Problema: {idea.problem}
Usuarios objetivo: {idea.target_users}
{arch_line}
{level_line}
Necesita auth: {idea.needs_auth} | Panel admin: {idea.needs_admin_panel} | IA: {idea.needs_ai}

Requisitos funcionales:
{req_lines}

Historias de usuario:
{story_lines if story_lines else "  (ninguna proporcionada)"}

IMPORTANTE: Genera la especificación COMPLETA incluyendo data_entities, api_endpoints, business_rules y dev_steps.
Los dev_steps deben usar los comandos reales del stack de la arquitectura elegida."""


# ── Agent ─────────────────────────────────────────────────────────────────────────

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
                    return OpenSpecResponse(project_name=idea.name, spec=doc.model_dump())
            except Exception as exc:
                logger.warning("LLM openspec generation failed, using fallback: %s", exc)

        return self._deterministic_generate(idea, requirements)

    # ── Conversion helpers ─────────────────────────────────────────────────────

    def _llm_output_to_doc(
        self,
        output: _OpenSpecLLMOutput,
        idea: IdeaRequest,
        requirements: RequirementsResponse,
    ) -> OpenSpecDoc:
        architecture = self._build_architecture(idea.architecture_type)
        milestones   = output.milestones if len(output.milestones) >= 3 else _DEFAULT_MILESTONES

        dm = output.data_model
        entities = [
            OpenSpecDataEntity(name=e.name, description=e.description, fields=e.fields, relations=e.relations)
            for e in output.data_entities
        ]
        data_model = OpenSpecDataModel(
            storage_type=dm.storage_type,
            technology=dm.technology,
            justification=dm.justification,
            orm=dm.orm,
            orm_rationale=dm.orm_rationale,
            relationships=[
                OpenSpecRelationship(
                    from_entity=r.from_entity, to_entity=r.to_entity, type=r.type,
                    through=r.through, cascade_delete=r.cascade_delete, optional=r.optional, label=r.label,
                )
                for r in dm.relationships
            ],
            indexes=dm.indexes,
            mermaid_diagram=dm.mermaid_diagram or self._generate_mermaid(entities),
            seed_needed=dm.seed_needed,
            seed_instructions=dm.seed_instructions,
            security_notes=dm.security_notes,
            mvp_scope=dm.mvp_scope,
            future_scope=dm.future_scope,
        )

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
                OpenSpecRequirement(id=r.id, title=r.title, description=r.description, acceptance_criteria=r.acceptance_criteria)
                for r in output.requirements
            ] or self._map_requirements(requirements),
            user_stories=[
                OpenSpecUserStory(id=s.id, actor=s.actor, goal=s.goal, benefit=s.benefit)
                for s in output.user_stories
            ] or self._map_user_stories(requirements),
            modules=output.modules or self._infer_modules(idea, requirements),
            milestones=milestones,
            data_entities=entities,
            data_model=data_model,
            api_endpoints=[
                OpenSpecApiEndpoint(
                    method=e.method, path=e.path, description=e.description,
                    auth_required=e.auth_required, request_body=e.request_body, response=e.response,
                )
                for e in output.api_endpoints
            ],
            business_rules=output.business_rules,
            dev_steps=[
                OpenSpecDevStep(step=s.step, title=s.title, description=s.description, commands=s.commands)
                for s in output.dev_steps
            ],
            constraints=OpenSpecConstraints(delivery=output.delivery, environments=output.environments),
        )

    def _deterministic_generate(
        self,
        idea: IdeaRequest,
        requirements: RequirementsResponse,
    ) -> OpenSpecResponse:
        architecture = self._build_architecture(idea.architecture_type)

        entities = self._infer_entities(idea, requirements)
        doc = OpenSpecDoc(
            project=OpenSpecProject(
                name=idea.name,
                sector=idea.sector,
                target_users=idea.target_users,
                problem=idea.problem,
                description=(
                    f"{idea.name} es una aplicación para el sector {idea.sector} "
                    f"que resuelve: {idea.problem}. Dirigida a: {idea.target_users}."
                ),
            ),
            architecture=architecture,
            requirements=self._map_requirements(requirements),
            user_stories=self._map_user_stories(requirements),
            modules=self._infer_modules(idea, requirements),
            milestones=_DEFAULT_MILESTONES,
            data_entities=entities,
            data_model=self._infer_data_model(idea, entities),
            api_endpoints=self._infer_endpoints(idea),
            business_rules=self._infer_business_rules(idea),
            dev_steps=self._infer_dev_steps(idea),
            constraints=OpenSpecConstraints(
                delivery="MVP dockerizado y documentado",
                environments=["desarrollo", "producción"],
            ),
        )
        return OpenSpecResponse(project_name=idea.name, spec=doc.model_dump())

    # ── Static builders ────────────────────────────────────────────────────────

    @staticmethod
    def _build_architecture(architecture_type: str | None) -> OpenSpecArchitecture:
        if not architecture_type:
            return OpenSpecArchitecture()
        meta = _ARCH_META.get(architecture_type)
        if meta is None:
            return OpenSpecArchitecture(type=architecture_type)
        name, stack, difficulty = meta
        return OpenSpecArchitecture(type=architecture_type, name=name, stack=stack, difficulty=difficulty)

    @staticmethod
    def _map_requirements(requirements: RequirementsResponse) -> list[OpenSpecRequirement]:
        return [
            OpenSpecRequirement(
                id=r.id,
                title=r.title,
                description=r.description,
                acceptance_criteria=[
                    f"El sistema implementa correctamente: {r.title}",
                    "La funcionalidad está cubierta por tests unitarios e integración",
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

    @staticmethod
    def _infer_entities(idea: IdeaRequest, requirements: RequirementsResponse) -> list[OpenSpecDataEntity]:
        entities: list[OpenSpecDataEntity] = []

        if idea.needs_auth:
            entities.append(OpenSpecDataEntity(
                name="User",
                description="Usuario autenticado en la plataforma",
                fields=[
                    "id: UUID PRIMARY KEY DEFAULT gen_random_uuid()",
                    "email: VARCHAR(255) UNIQUE NOT NULL",
                    "password_hash: VARCHAR(255) NOT NULL",
                    "name: VARCHAR(100) NOT NULL",
                    "created_at: TIMESTAMPTZ DEFAULT now()",
                ],
                relations=["has_many Projects" if "proyecto" in idea.problem.lower() else ""],
            ))

        for feature in idea.core_features[:3]:
            name = feature.split()[0].capitalize()
            if name not in {e.name for e in entities}:
                entities.append(OpenSpecDataEntity(
                    name=name,
                    description=f"Entidad principal para: {feature}",
                    fields=[
                        "id: UUID PRIMARY KEY DEFAULT gen_random_uuid()",
                        "user_id: UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE",
                        "name: VARCHAR(255) NOT NULL",
                        "status: VARCHAR(50) DEFAULT 'active'",
                        "created_at: TIMESTAMPTZ DEFAULT now()",
                        "updated_at: TIMESTAMPTZ DEFAULT now()",
                    ],
                    relations=["belongs_to User"],
                ))

        return entities

    @staticmethod
    def _infer_endpoints(idea: IdeaRequest) -> list[OpenSpecApiEndpoint]:
        endpoints: list[OpenSpecApiEndpoint] = []

        if idea.needs_auth:
            endpoints += [
                OpenSpecApiEndpoint(method="POST", path="/api/auth/register", description="Registro de usuario", auth_required=False, request_body="{ email, password, name }", response="201 { access_token, user }"),
                OpenSpecApiEndpoint(method="POST", path="/api/auth/login", description="Login con email y contraseña", auth_required=False, request_body="{ email, password }", response="200 { access_token, user }"),
                OpenSpecApiEndpoint(method="GET", path="/api/auth/me", description="Perfil del usuario autenticado", auth_required=True, response="200 { user }"),
            ]

        resource = idea.name.lower().replace(" ", "-")
        endpoints += [
            OpenSpecApiEndpoint(method="GET",    path=f"/api/{resource}",      description="Lista paginada de recursos del usuario", auth_required=True, response=f"200 {{ data: {idea.name.split()[0]}[], total, page }}"),
            OpenSpecApiEndpoint(method="POST",   path=f"/api/{resource}",      description="Crear nuevo recurso", auth_required=True, request_body="{ ...campos }",       response="201 { id, ...campos }"),
            OpenSpecApiEndpoint(method="GET",    path=f"/api/{resource}/:id",  description="Obtener recurso por ID", auth_required=True, response="200 { id, ...campos }"),
            OpenSpecApiEndpoint(method="PUT",    path=f"/api/{resource}/:id",  description="Actualizar recurso", auth_required=True, request_body="{ ...campos }",        response="200 { id, ...campos }"),
            OpenSpecApiEndpoint(method="DELETE", path=f"/api/{resource}/:id",  description="Eliminar recurso", auth_required=True, response="204 No Content"),
        ]

        return endpoints

    @staticmethod
    def _infer_business_rules(idea: IdeaRequest) -> list[str]:
        rules = [
            "Un usuario solo puede acceder y modificar sus propios recursos (aislamiento por userId)",
        ]
        if idea.needs_auth:
            rules += [
                "El email debe ser único — el registro rechaza emails duplicados con 409 Conflict",
                "Las contraseñas deben tener mínimo 8 caracteres, una mayúscula, un número y un símbolo especial",
                "Los tokens JWT expiran en 15 minutos; el refresh token rota y expira en 7 días",
            ]
        rules += [
            "Los recursos eliminados no se recuperan (hard delete); informar al usuario antes de la operación",
            "Todas las respuestas de error incluyen un campo 'message' en español descriptivo",
        ]
        return rules

    @staticmethod
    def _infer_data_model(idea: IdeaRequest, entities: list[OpenSpecDataEntity]) -> OpenSpecDataModel:
        db_info = _ARCH_DB.get(idea.architecture_type or "", ("PostgreSQL", _ORM_PRISMA, _RATIONALE_PRISMA))
        technology, orm, orm_rationale = db_info

        relationships: list[OpenSpecRelationship] = []
        for entity in entities:
            for rel in entity.relations:
                if not rel:
                    continue
                parts = rel.split()
                if len(parts) < 2:
                    continue
                rel_type_word, target = parts[0].lower(), parts[1]
                if rel_type_word == "has_many":
                    relationships.append(OpenSpecRelationship(
                        from_entity=entity.name, to_entity=target,
                        type="one_to_many", cascade_delete=True,
                    ))
                elif rel_type_word == "belongs_to":
                    # already captured from the other side; skip to avoid duplicates
                    pass

        entity_names = [e.name for e in entities]
        indexes = [f"CREATE UNIQUE INDEX idx_{e.name.lower()}s_email ON {e.name.lower()}s(email)"
                   for e in entities if any("email" in f.lower() for f in e.fields)]
        for entity in entities[1:]:
            indexes.append(
                f"CREATE INDEX idx_{entity.name.lower()}s_user_id ON {entity.name.lower()}s(user_id)"
            )

        security_notes = [
            "Contraseñas almacenadas con bcrypt (mínimo 12 rondas) — nunca en texto plano.",
            "Claves de API y secretos solo en variables de entorno (.env), nunca en código fuente.",
            "Cada query filtra por userId para garantizar aislamiento de datos entre usuarios.",
        ]
        if idea.needs_auth:
            security_notes.append("Tokens JWT con expiración corta (15 min); refresh token rotativo con expiración en 7 días.")

        return OpenSpecDataModel(
            storage_type="relational",
            technology=technology,
            justification=(
                f"{technology} es ideal para este MVP: los datos del proyecto ({', '.join(entity_names[:3])}) "
                f"tienen relaciones claras y requieren integridad referencial. "
                f"Es compatible con el stack seleccionado y tiene excelente soporte en Docker."
            ),
            orm=orm,
            orm_rationale=orm_rationale,
            relationships=relationships,
            indexes=indexes,
            mermaid_diagram=OpenSpecAgent._generate_mermaid(entities),
            seed_needed=True,
            seed_instructions=[
                "Ejecutar migraciones: npx prisma migrate dev --name init  (o equivalente del ORM elegido)",
                "Ejecutar seeds:       npx prisma db seed  (o python manage.py loaddata initial_data.json)",
                "Usuario de prueba:    admin@example.local  (contraseña definida en .env, no hardcodeada)",
            ],
            security_notes=security_notes,
            mvp_scope=entity_names,
            future_scope=["AuditLog", "Notification", "ActivityFeed"],
        )

    @staticmethod
    def _generate_mermaid(entities: list[OpenSpecDataEntity]) -> str:
        if not entities:
            return ""

        lines = ["erDiagram"]

        # Relationship lines
        for entity in entities:
            for rel in entity.relations:
                if not rel:
                    continue
                parts = rel.split()
                if len(parts) < 2:
                    continue
                rel_type_word, target = parts[0].lower(), parts[1]
                if rel_type_word == "has_many":
                    lines.append(f'    {entity.name.upper()} ||--o{{ {target.upper()} : ""')
                elif rel_type_word == "belongs_to":
                    lines.append(f'    {target.upper()} ||--o{{ {entity.name.upper()} : ""')
        lines.append("")

        # Entity blocks (up to 7 fields each for readability)
        _TYPE_MAP = {
            "uuid": "uuid", "varchar": "string", "text": "string", "string": "string",
            "int": "int", "bigint": "int", "bool": "boolean", "boolean": "boolean",
            "timestamp": "datetime", "timestamptz": "datetime", "datetime": "datetime",
            "date": "date", "decimal": "float", "numeric": "float", "float": "float",
            "json": "json", "jsonb": "json",
        }
        for entity in entities:
            lines.append(f"    {entity.name.upper()} {{")
            for field_str in entity.fields[:7]:
                parts = field_str.split(":", 1)
                if len(parts) != 2:
                    continue
                fname = parts[0].strip()
                fdef  = parts[1].strip().lower()
                ftype = next((v for k, v in _TYPE_MAP.items() if k in fdef), "string")
                constraint = ""
                if "primary key" in fdef or fname == "id":
                    constraint = " PK"
                elif "unique" in fdef:
                    constraint = " UK"
                elif "references" in fdef or fname.endswith("_id"):
                    constraint = " FK"
                lines.append(f"        {ftype} {fname}{constraint}")
            lines.append("    }")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _infer_dev_steps(idea: IdeaRequest) -> list[OpenSpecDevStep]:
        return [
            OpenSpecDevStep(
                step=1,
                title="Configurar proyecto y entorno Docker",
                description="Crear estructura base, Docker Compose con DB y configurar variables de entorno",
                commands=["cp .env.example .env", "docker compose up -d postgres redis", "npm install"],
            ),
            OpenSpecDevStep(
                step=2,
                title="Definir modelos y ejecutar migraciones",
                description="Crear los modelos del dominio en el ORM y ejecutar las migraciones iniciales",
                commands=["npx prisma migrate dev --name init", "npx prisma generate"],
            ),
            OpenSpecDevStep(
                step=3,
                title="Implementar autenticación",
                description="Crear endpoints de registro y login con JWT; proteger rutas privadas",
                commands=["npm run test:auth"],
            ),
            OpenSpecDevStep(
                step=4,
                title="Implementar lógica de negocio principal",
                description=f"Crear los endpoints y servicios para las funcionalidades principales: {', '.join(idea.core_features[:3])}",
                commands=["npm run test"],
            ),
            OpenSpecDevStep(
                step=5,
                title="Frontend e integración API",
                description="Conectar la interfaz de usuario con el backend; implementar formularios y listados principales",
                commands=["npm run dev"],
            ),
            OpenSpecDevStep(
                step=6,
                title="Testing y despliegue",
                description="Ejecutar suite de tests completa; preparar Docker para producción; desplegar en Railway/Render",
                commands=["npm run test", "docker compose -f docker-compose.prod.yml up --build"],
            ),
        ]
