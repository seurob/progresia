"""Tutorial schema: step-by-step implementation guide derived from an OpenSpec."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TutorialStep(BaseModel):
    action: str
    command: str | None = None
    notes: str | None = None


class TutorialPhase(BaseModel):
    title: str
    description: str
    steps: list[TutorialStep]


class TutorialRequest(BaseModel):
    project_name: str
    sector: str
    architecture_type: str
    stack: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    requirements: list[dict] = Field(default_factory=list)
    needs_auth: bool = True
    needs_admin_panel: bool = True


class TutorialResponse(BaseModel):
    project_name: str
    architecture_type: str
    phases: list[TutorialPhase]
    total_steps: int
