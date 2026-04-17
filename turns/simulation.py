from models.path import Path
from models.map import Map
from models.hub import Hub
from models.drone import Drone


class Simulator:
    def __init__(self, map: Map, path: Path) -> None:
        self.map = map
        self.path = path
        self.nb_drones = self.map.nb_drones
        self.hub_occ: dict[Hub, int] = {h: 0 for h in self.map.hubs}
        # all drones start here
        self.hub_occ[self.map.start_hub] = self.nb_drones

    def _snapshot(self, drones: list[Drone]) -> dict[Hub, list[int]]:
        """Snapshot current drone positions as hub -> list of drone_ids."""
        snap: dict[Hub, list[int]] = {h: [] for h in self.map.hubs}
        for drone in drones:
            snap[drone.current_hub].append(drone.drone_id)
        return snap

    def simulate(self) -> tuple[list[dict[Hub, list[int]]], list[str]]:
        drones = [Drone(i + 1, self.path) for i in range(self.nb_drones)]
        turns: list[dict[Hub, list[int]]] = []
        output: list[str] = []
        end = self.map.end_hub

        # 1st snapshot, before any movement
        turns.append(self._snapshot(drones))

        while self.hub_occ.get(end, 0) < self.nb_drones:
            turn_moves: list[str] = []

            for drone in drones:
                if drone.arrived:
                    continue

                next_hub = drone.next_hub

                if next_hub is None:
                    continue

                # check capacity of next hub
                if self.hub_occ.get(next_hub, 0) >= next_hub.max_drones:
                    continue  # hub full, drone waits

                # drone in transit (restricted hub turn 2) — must complete move
                if drone.in_transit:
                    self.hub_occ[drone.current_hub] -= 1
                    drone.move()
                    self.hub_occ[drone.current_hub] += 1
                    continue

                # move drone
                self.hub_occ[drone.current_hub] -= 1
                drone.move()
                turn_moves.append(
                    f"D{drone.drone_id}-"
                    f"{self.path.hubs[drone.path_index].name}"
                )
                if not drone.in_transit:
                    self.hub_occ[drone.current_hub] += 1

            if turn_moves:
                output.append(" ".join(turn_moves))

            # snapshot after all drones have moved this turn
            turns.append(self._snapshot(drones))

        return turns, output
