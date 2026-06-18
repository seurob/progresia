from app.schemas.idea import IdeaRequest
from app.schemas.requirements import RequirementItem, RequirementsResponse, UserStory


class RequirementsAgent:
    def generate(self, idea: IdeaRequest) -> RequirementsResponse:
        functional = [
            RequirementItem(
                id=f"RF-{index + 1:03}",
                title=feature,
                description=f"El sistema debe permitir gestionar: {feature}.",
            )
            for index, feature in enumerate(idea.core_features)
        ]

        stories = [
            UserStory(
                id=f"US-{index + 1:03}",
                actor="Usuario principal",
                goal=feature,
                benefit="validar la propuesta de valor del MVP",
            )
            for index, feature in enumerate(idea.core_features)
        ]

        return RequirementsResponse(
            project_name=idea.name,
            functional_requirements=functional,
            non_functional_requirements=[
                RequirementItem(
                    id="RNF-001",
                    title="Seguridad básica",
                    description="La plataforma debe proteger rutas privadas y validar entradas.",
                ),
                RequirementItem(
                    id="RNF-002",
                    title="Despliegue reproducible",
                    description="El MVP debe poder levantarse localmente con Docker Compose.",
                ),
            ],
            user_stories=stories,
        )
