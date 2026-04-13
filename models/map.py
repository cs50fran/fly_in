from models.hub import Hub
from models.connection import Connection
from pydantic import BaseModel, Field


class Map(BaseModel):
    nb_drones: int = Field(ge=1)
    hubs: list[Hub]
    connections: list[Connection]

    def get_hub(self, name: str) -> Hub | str:
        for hub in self.hubs:
            if name == hub.name:
                return hub
        return f"{name} not in map"


    def get_connections(self, hub: Hub) -> list[Connection] | str:
        res: list[Connection] = []
        for c in self.connections:
            if c.zone1 == hub.name or c.zone2 == hub.name:
                res.append(c)
        if res == []:
            return f"{hub} does not have any connection on this map"
        return res 


    def get_start(self) -> Hub | str:
        for hub in self.hubs:
            if hub.is_start:
                return hub
        return "could not find start hub"
            


    def get_end(self) -> Hub | str:
        for hub in self.hubs:
            if hub.is_end:
                return hub
        return "could not find end hub"  
