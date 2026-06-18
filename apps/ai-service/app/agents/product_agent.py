from app.schemas.idea import IdeaRequest


class ProductAgent:
    """Primer agente determinista para estabilizar el contrato antes de integrar LLMs."""

    def analyze(self, idea: IdeaRequest) -> dict[str, object]:
        return {
            "summary": f"{idea.name} resuelve {idea.problem.lower()} para {idea.target_users}.",
            "target_users": idea.target_users,
            "value_proposition": f"Reducir fricción operativa en el sector {idea.sector}.",
            "mvp_scope": idea.core_features[:5],
            "risks": [
                "Alcance demasiado amplio para una primera versión.",
                "Falta de validación temprana con usuarios reales.",
            ],
        }
