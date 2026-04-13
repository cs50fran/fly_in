from models.hub import Hub
from models.connection import Connection
from pydantic import BaseModel, model_validator

class Path(BaseModel):
    hubs: list[Hub]
    connections: list[Connection]


    @model_validator(mode='after')
    def validate_path(self):
        if len(self.connections) != len(self.hubs) - 1:
            raise ValueError("something is wrong with the path")
        return self