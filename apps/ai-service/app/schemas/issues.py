from pydantic import BaseModel, Field


class GitHubIssue(BaseModel):
    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    priority: str = "medium"  # high | medium | low
    milestone: str | None = None


class IssueGenerationRequest(BaseModel):
    project_name: str
    sector: str
    openspec: dict = Field(default_factory=dict)


class IssueGenerationResponse(BaseModel):
    project_name: str
    milestones: list[str]
    issues: list[GitHubIssue]
    total: int
