from models.hub import Hub
from models.connection import Connection
from pydantic import BaseModel, model_validator


class Path(BaseModel):
    hubs: list[Hub]

    @model_validator(mode='after')
    def validate_path(self) -> 'Path':
        if len(self.hubs) < 2:
            raise ValueError("Path must have at least a start and an end hub")
        return self
