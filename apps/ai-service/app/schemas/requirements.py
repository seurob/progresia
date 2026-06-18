from pydantic import BaseModel


class RequirementItem(BaseModel):
    id: str
    title: str
    description: str


class UserStory(BaseModel):
    id: str
    actor: str
    goal: str
    benefit: str


class RequirementsResponse(BaseModel):
    project_name: str
    functional_requirements: list[RequirementItem]
    non_functional_requirements: list[RequirementItem]
    user_stories: list[UserStory]
