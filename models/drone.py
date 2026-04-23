from models.hub import Hub, ZoneType
from models.path import Path


class Drone:
    def __init__(self, drone_id: int, path: Path) -> None:
        self.drone_id: int = drone_id
        self.path: Path = path
        self.path_index: int = 0
        # True while drone is on the connection toward a restricted hub
        self.in_transit: bool = False
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

        if self.in_transit:
            # Phase 2: complete the restricted transit — arrive at the hub
            self.path_index += 1
            if self.path_index == len(self.path.hubs) - 1:
                self.arrived = True
            self.in_transit = False
            return

        next = self.next_hub
        if next is None:
            self.arrived = True
            return

        if next.zone_type == ZoneType.restricted:
            # Phase 1: start restricted transit, don't arrive yet
            self.in_transit = True
            return  # path_index NOT incremented

        # Normal move
        self.path_index += 1
        if self.path_index == len(self.path.hubs) - 1:
            self.arrived = True
