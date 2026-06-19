from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):
    path: str = Field(description="Relative file path, e.g. src/app.module.ts")
    language: str = Field(description="Language or format: typescript, python, yaml, markdown, json")
    content: str = Field(description="Full file content")


class CodeGenerationRequest(BaseModel):
    project_name: str
    sector: str
    modules: list[str] = Field(default_factory=list)
    requirements: list[dict] = Field(default_factory=list)
    needs_auth: bool = True
    needs_admin_panel: bool = True
    needs_ai: bool = False
    stack: list[str] = Field(
        default_factory=lambda: ["React", "NestJS", "PostgreSQL", "FastAPI", "Docker"]
    )
    # Optional: explicit architecture type from the architecture recommender.
    # When set, codegen bypasses LLM and picks the matching template directly.
    architecture_type: str | None = None


class CodeGenerationResponse(BaseModel):
    project_name: str
    files: list[GeneratedFile]
