from typing import Any

from pydantic import BaseModel


class OpenSpecResponse(BaseModel):
    project_name: str
    spec: dict[str, Any]
