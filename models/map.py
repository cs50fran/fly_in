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
                f"hub '{hub.name}' does not have any neighbours on this map"
            )
        return res


    # def get_connection(self, hub1: Hub, hub2: Hub) -> Connection:
    #     for c in self.connections:
    #         if c.zone1 == hub1.name or c.zone2 == hub1.name:
    #             if c.zone1 == hub2 or c.zone2 == hub2:
    #                 return c
    #     raise ValueError (
    #         f"hubs '{hub1.name}', '{hub2.name} do not have any connections"
    #         " on this map"
    #         )
