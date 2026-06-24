from pydantic import BaseModel, Field


class IdeaRequest(BaseModel):
    name: str = Field(min_length=2)
    sector: str = Field(min_length=2)
    problem: str = Field(min_length=10)
    target_users: str = Field(min_length=2)
    core_features: list[str] = Field(min_length=1)
    needs_auth: bool = True
    needs_admin_panel: bool = True
    needs_ai: bool = False
    # BEGINNER | INTERMEDIATE | ADVANCED — drives architecture complexity and tutorial depth
    technical_level: str = "INTERMEDIATE"
    # Injected by NestJS when a stored architecture recommendation exists
    architecture_type: str | None = None
    # web | mobile | desktop | api | saas | ai_tool — constrains stack selection
    product_type: str = "web"
