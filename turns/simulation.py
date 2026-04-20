from models.path import Path
from models.map import Map
from models.hub import Hub
from models.drone import Drone
from models.connection import Connection


class Simulator:
    def __init__(self, map: Map, path: Path) -> None:
        self.map = map
        self.path = path
        self.nb_drones = self.map.nb_drones
        self.hub_occ: dict[Hub, int] = {h: 0 for h in self.map.hubs}
        # all drones start here
        self.hub_occ[self.map.start_hub] = self.nb_drones

    def _snapshot(self, drones: list[Drone]) -> tuple[dict[Hub, list[int]], set[int]]:
        """Snapshot current drone positions as hub -> list of drone_ids, plus in_transit set."""
        snap: dict[Hub, list[int]] = {h: [] for h in self.map.hubs}
        in_transit: set[int] = set()
        for drone in drones:
            snap[drone.current_hub].append(drone.drone_id)
            if drone.in_transit:
                in_transit.add(drone.drone_id)
        return snap, in_transit
    
    @property
    def _path_connections(self) -> list[Connection]:
        hubs = self.path.hubs
        map = self.map
        connections = self.map.connections

        path_connections = []
        for i in range(len(hubs) - 1):
            path_connections.append(map.get_connection(hubs[i], hubs[i + 1]))
        return path_connections


    def simulate(self) -> tuple[list[dict[Hub, list[int]]], list[set[int]], list[str]]:
        drones = [Drone(i + 1, self.path) for i in range(self.nb_drones)]
        turns: list[dict[Hub, list[int]]] = []
        in_transit_turns: list[set[int]] = []
        output: list[str] = []
        end = self.map.end_hub

        # 1st snapshot, before any movement
        snap, in_transit = self._snapshot(drones)
        turns.append(snap)
        in_transit_turns.append(in_transit)

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
                if drone.in_transit:
                    turn_moves.append(
                        f"D{drone.drone_id}-"
                        f"{self.path.hubs[drone.path_index].name}-"
                        f"{self.path.hubs[drone.path_index + 1].name}"
                    )
                else:
                    turn_moves.append(
                        f"D{drone.drone_id}-"
                        f"{self.path.hubs[drone.path_index].name}"
                    )
                if not drone.in_transit:
                    self.hub_occ[drone.current_hub] += 1

            if turn_moves:
                output.append(" ".join(turn_moves))

            # snapshot after all drones moved this turn
            snap, in_transit = self._snapshot(drones)
            turns.append(snap)
            in_transit_turns.append(in_transit)

        return turns, in_transit_turns, output
