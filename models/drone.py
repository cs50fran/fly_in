from models.hub import Hub, ZoneType
from models.path import Path


class Drone:
    def __init__(self, drone_id: int, path: Path) -> None:
        self.drone_id: int = drone_id
        self.path: Path = path
        self.path_index: int = 0
        self.in_transit: bool = False  # True on 1st pass to restricted zone
        self.arrived: bool = False

    @property
    def current_hub(self) -> Hub:
        return self.path.hubs[self.path_index]

    @property
    def next_hub(self) -> Hub | None:
        next_index = self.path_index + 1
        if next_index >= len(self.path.hubs):
            return None
        return self.path.hubs[next_index]

    def move(self) -> None:
        if self.arrived:
            return

        # second turn of restricted zone crossing — complete the move
        if self.in_transit:
            self.path_index += 1
            self.in_transit = False
            if self.path_index == len(self.path.hubs) - 1:
                self.arrived = True
            return

        next = self.next_hub
        if next is None:
            self.arrived = True
            return

        if next.zone_type == ZoneType.restricted:
            # first turn: mark in transit, don't advance index yet
            # Acho que eu tenho de mudar isto. 
            #Ele devia libertar a zona logo e ocupar a conexão. 
            self.in_transit = True
        else:
            self.path_index += 1
            if self.path_index == len(self.path.hubs) - 1:
                self.arrived = True
