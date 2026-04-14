from models.hub import Hub
from models.connection import Connection
from pydantic import BaseModel, Field


class Map(BaseModel):
    nb_drones: int = Field(ge=1)
    start_hub: Hub
    end_hub: Hub
    hubs: list[Hub]
    connections: list[Connection]

    def get_hub(self, name: str) -> Hub:
        for hub in self.hubs:
            if name == hub.name:
                return hub
        raise ValueError(f"{name} not in map")


    def get_connections(self, hub: Hub) -> list[Connection]:
        res: list[Connection] = []
        for c in self.connections:
            if c.zone1 == hub.name or c.zone2 == hub.name:
                res.append(c)
        if res == []:
            raise ValueError (
                f"{hub} does not have any connection on this map"
                )
        return res
    
    def get_neighbours(self, hub: Hub) -> list[Hub]:
        res: list[Hub] = []
        for c in self.connections:
            if c.zone1 == hub.name:
                neighbour = self.get_hub(c.zone2)
                res.append(neighbour)
            elif c.zone2 == hub.name:
                neighbour = self.get_hub(c.zone1)
                res.append(neighbour)
        if res == []:
            raise ValueError(
                f"{hub} does not have any neighbours on this map"
            )
        return res
