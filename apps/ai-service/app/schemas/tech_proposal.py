from pydantic import BaseModel, Field


class TechProposalRequest(BaseModel):
    name: str = Field(min_length=1)
    sector: str = Field(default="Tecnologia e IT")
    level: str = Field(default="INTERMEDIATE")  # BEGINNER | INTERMEDIATE
    product_type: str = Field(default="web")
    main_objective: str = Field(default="mvp")
    architecture_style: str = Field(default="frontend_api")
    data_needs: list[str] = Field(default_factory=list)
    ai_needs: str = Field(default="none")
    deployment_target: str = Field(default="docker_local")
    core_features: list[str] = Field(default_factory=list)
    mandatory_techs: str | None = Field(default=None, description="Free-text mandatory technologies the user explicitly requested")


class TechProposal(BaseModel):
    id: int
    name: str
    tagline: str
    stack: list[str]
    difficulty: str  # "Principiante" | "Intermedio"
    description: str
    advantages: list[str]
    limitations: list[str]
    recommended_for: str
    learning_outcomes: list[str]
    docker_ready: bool
    ai_ready: bool
    estimated_setup_minutes: int


class TechProposalResponse(BaseModel):
    proposals: list[TechProposal]
    recommended_id: int
    recommendation_reason: str
