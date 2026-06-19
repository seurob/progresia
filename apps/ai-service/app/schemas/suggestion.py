from pydantic import BaseModel


class FeatureSuggestionRequest(BaseModel):
    sector: str
    problem: str
    target_users: str


class FeatureSuggestionResponse(BaseModel):
    features: list[str]
