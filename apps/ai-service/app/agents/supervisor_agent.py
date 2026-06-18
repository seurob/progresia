from app.schemas.idea import IdeaRequest


class SupervisorAgent:
    def next_step(self, idea: IdeaRequest) -> str:
        if len(idea.core_features) < 2:
            return "ask_more_questions"
        return "generate_requirements"
