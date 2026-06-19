"""OpenSpec: the canonical specification document that drives everything downstream.

Flow:
  IdeaRequest + ArchitectureRecommendation
       ↓  OpenSpecAgent
    OpenSpecDoc  (this file)
       ↓
  IssueGeneratorAgent  →  GitHub Issues
  CodeGenerationAgent  →  code templates
  TutorialAgent        →  step-by-step guide
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Building blocks ────────────────────────────────────────────────────────────

class OpenSpecProject(BaseModel):
    name: str
    sector: str
    target_users: str
    problem: str
    description: str = ""


class OpenSpecArchitecture(BaseModel):
    """Embedded architecture decision — sourced from ArchitectureAgent output."""
    type: str = ""          # e.g. "DJANGO_REST", "NEXTJS_APP"
    name: str = ""          # e.g. "Django 5 + DRF"
    stack: list[str] = Field(default_factory=list)   # ["Django 5", "PostgreSQL 16", ...]
    difficulty: str = ""    # BEGINNER | INTERMEDIATE | ADVANCED


class OpenSpecRequirement(BaseModel):
    id: str                                                         # RF-001
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)   # ["El sistema debe...", ...]


class OpenSpecUserStory(BaseModel):
    id: str         # US-001
    actor: str
    goal: str
    benefit: str


class OpenSpecModule(BaseModel):
    name: str
    description: str = ""


class OpenSpecConstraints(BaseModel):
    delivery: str = "MVP dockerizado y documentado"
    environments: list[str] = Field(default_factory=lambda: ["desarrollo", "producción"])


# ── The canonical document ─────────────────────────────────────────────────────

class OpenSpecDoc(BaseModel):
    """Single source of truth for a project's specification.

    Every downstream agent (Issues, Code, Tutorial) reads from this document.
    Keys are stable — no guessing between 'requirements' vs 'functional_requirements'.
    """
    project:      OpenSpecProject
    architecture: OpenSpecArchitecture = Field(default_factory=OpenSpecArchitecture)
    requirements: list[OpenSpecRequirement] = Field(default_factory=list)
    user_stories: list[OpenSpecUserStory]   = Field(default_factory=list)
    modules:      list[str]                 = Field(default_factory=list)
    milestones:   list[str]                 = Field(default_factory=list)
    constraints:  OpenSpecConstraints       = Field(default_factory=OpenSpecConstraints)

    # Injected by the NestJS API layer, not by the AI agent
    generated_by: str = "ai-service"

    def default_milestones(self) -> list[str]:
        return [
            "Milestone 1: Setup y arquitectura",
            "Milestone 2: Modelos y base de datos",
            "Milestone 3: API y lógica de negocio",
            "Milestone 4: Frontend y UX",
            "Milestone 5: Testing y despliegue",
        ]


# ── API response wrapper ───────────────────────────────────────────────────────

class OpenSpecResponse(BaseModel):
    project_name: str
    spec: dict[str, Any]   # OpenSpecDoc serialized — kept as dict for Prisma JSON storage
