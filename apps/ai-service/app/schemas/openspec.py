"""OpenSpec: the canonical specification document that drives everything downstream.

Flow:
  IdeaRequest + ArchitectureRecommendation
       ↓  OpenSpecAgent
    OpenSpecDoc  ← this file: the single source of truth
       ↓
  IssueGeneratorAgent  →  GitHub Issues
  CodeGenerationAgent  →  code templates
  TutorialAgent        →  step-by-step guide with real commands
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Project ────────────────────────────────────────────────────────────────────

class OpenSpecProject(BaseModel):
    name: str
    sector: str
    target_users: str
    problem: str
    description: str = ""


# ── Architecture ───────────────────────────────────────────────────────────────

class OpenSpecArchitecture(BaseModel):
    type: str = ""          # e.g. "DJANGO_REST", "NEXTJS_APP"
    name: str = ""          # e.g. "Django 5 + DRF"
    stack: list[str] = Field(default_factory=list)
    difficulty: str = ""    # BEGINNER | INTERMEDIATE | ADVANCED


# ── Functional requirements ────────────────────────────────────────────────────

class OpenSpecRequirement(BaseModel):
    id: str                                                          # RF-001
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class OpenSpecUserStory(BaseModel):
    id: str          # US-001
    actor: str
    goal: str
    benefit: str


# ── Data model ─────────────────────────────────────────────────────────────────

class OpenSpecDataEntity(BaseModel):
    """A domain entity with its fields and relationships.

    Fields use a concise SQL-like notation:
      "id: UUID PK DEFAULT gen_random_uuid()"
      "email: VARCHAR(255) UNIQUE NOT NULL"
      "created_at: TIMESTAMPTZ DEFAULT now()"
    """
    name: str
    description: str = ""
    fields: list[str] = Field(default_factory=list)
    relations: list[str] = Field(default_factory=list)   # "has_many Orders", "belongs_to User"


class OpenSpecRelationship(BaseModel):
    from_entity: str
    to_entity: str
    type: str = "one_to_many"   # one_to_one | one_to_many | many_to_many
    through: str = ""           # intermediate table name for many_to_many
    cascade_delete: bool = False
    optional: bool = False
    label: str = ""


class OpenSpecDataModel(BaseModel):
    """Rich data-persistence section — authoritative source for DB schema, ORM, and diagram."""
    storage_type: str = "relational"   # relational | document | vector | cache | graph | hybrid
    technology: str = "PostgreSQL"
    justification: str = ""
    orm: str = ""
    orm_rationale: str = ""
    relationships: list[OpenSpecRelationship] = Field(default_factory=list)
    indexes: list[str] = Field(default_factory=list)
    mermaid_diagram: str = ""
    seed_needed: bool = False
    seed_instructions: list[str] = Field(default_factory=list)
    security_notes: list[str] = Field(default_factory=list)
    mvp_scope: list[str] = Field(default_factory=list)    # entity names included in MVP
    future_scope: list[str] = Field(default_factory=list) # planned for later phases


# ── API contract ───────────────────────────────────────────────────────────────

class OpenSpecApiEndpoint(BaseModel):
    method: str            # GET | POST | PUT | PATCH | DELETE
    path: str              # "/api/users/:id"
    description: str
    auth_required: bool = True
    request_body: str = ""
    response: str = ""


# ── Implementation plan ────────────────────────────────────────────────────────

class OpenSpecDevStep(BaseModel):
    step: int
    title: str
    description: str
    commands: list[str] = Field(default_factory=list)


# ── Delivery constraints ───────────────────────────────────────────────────────

class OpenSpecConstraints(BaseModel):
    delivery: str = "MVP dockerizado y documentado"
    environments: list[str] = Field(default_factory=lambda: ["desarrollo", "producción"])


# ── Canonical document ─────────────────────────────────────────────────────────

class OpenSpecDoc(BaseModel):
    """Single source of truth — every downstream agent reads from this.

    Keys are intentionally stable so agents can reference them without guessing:
      spec.requirements      → IssueGeneratorAgent + CodeGenerationAgent
      spec.architecture.type → CodeGenerationAgent template dispatch
      spec.architecture.stack → TutorialAgent command generation
      spec.data_entities     → CodeGenerationAgent DB schema
      spec.api_endpoints     → CodeGenerationAgent route generation
      spec.business_rules    → CodeGenerationAgent validation logic
      spec.dev_steps         → TutorialAgent ordered guide
    """
    project:        OpenSpecProject
    architecture:   OpenSpecArchitecture       = Field(default_factory=OpenSpecArchitecture)
    requirements:   list[OpenSpecRequirement]  = Field(default_factory=list)
    user_stories:   list[OpenSpecUserStory]    = Field(default_factory=list)
    modules:        list[str]                  = Field(default_factory=list)
    milestones:     list[str]                  = Field(default_factory=list)
    data_entities:  list[OpenSpecDataEntity]   = Field(default_factory=list)
    data_model:     OpenSpecDataModel          = Field(default_factory=OpenSpecDataModel)
    api_endpoints:  list[OpenSpecApiEndpoint]  = Field(default_factory=list)
    business_rules: list[str]                  = Field(default_factory=list)
    dev_steps:      list[OpenSpecDevStep]      = Field(default_factory=list)
    constraints:    OpenSpecConstraints        = Field(default_factory=OpenSpecConstraints)

    generated_by: str = "ai-service"


# ── API response wrapper ───────────────────────────────────────────────────────

class OpenSpecResponse(BaseModel):
    project_name: str
    spec: dict[str, Any]
