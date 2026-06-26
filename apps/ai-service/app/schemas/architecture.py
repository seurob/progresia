from pydantic import BaseModel, Field


class TechStackItem(BaseModel):
    name: str
    version: str
    purpose: str
    official_docs: str


class ArchitectureRequest(BaseModel):
    project_name: str
    sector: str
    problem: str
    target_users: str
    key_features: list[str] = Field(default_factory=list)
    needs_auth: bool = True
    needs_admin_panel: bool = True
    needs_ai: bool = False
    preferred_stack: str = Field(default="")
    # BEGINNER | INTERMEDIATE | ADVANCED — constrains which architectures to recommend
    technical_level: str = Field(default="INTERMEDIATE")
    # web | mobile | desktop | api | saas | ai_tool — bypasses LLM for mobile/desktop
    product_type: str = Field(default="web")
    architecture_style: str | None = Field(default=None)
    data_needs: list[str] = Field(default_factory=list)
    ai_needs: str | None = Field(default=None)
    deployment_target: str | None = Field(default=None)


class LearningResource(BaseModel):
    title: str
    url: str
    type: str  # "docs" | "course" | "book" | "video" | "article"
    level: str  # "BEGINNER" | "INTERMEDIATE" | "ADVANCED"


class UpgradeSignal(BaseModel):
    signal: str
    reason: str
    next_step: str


class ArchitectureRecommendation(BaseModel):
    architecture_type: str
    name: str
    justification: str
    tech_stack: list[TechStackItem]
    alternatives: list[str]
    difficulty: str  # BEGINNER | INTERMEDIATE | ADVANCED
    risks: list[str]
    first_steps: list[str]
    educational_notes: list[str]
    learning_path: list[LearningResource] = Field(default_factory=list)
    when_to_upgrade: list[UpgradeSignal] = Field(default_factory=list)
