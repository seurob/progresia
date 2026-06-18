from app.schemas.idea import IdeaRequest
from app.schemas.openspec import OpenSpecResponse
from app.schemas.requirements import RequirementsResponse


class OpenSpecAgent:
    def generate(self, idea: IdeaRequest, requirements: RequirementsResponse) -> OpenSpecResponse:
        spec = {
            "project": {
                "name": idea.name,
                "sector": idea.sector,
                "targetUsers": idea.target_users,
            },
            "requirements": [
                requirement.model_dump()
                for requirement in requirements.functional_requirements
            ],
            "constraints": {
                "stack": ["React", "NestJS", "PostgreSQL", "FastAPI", "Docker"],
                "delivery": "MVP desplegable y documentado",
            },
        }
        return OpenSpecResponse(project_name=idea.name, spec=spec)
