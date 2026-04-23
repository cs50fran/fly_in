from models.path import Path
from models.map import Map
from models.hub import Hub, ZoneType
from models.drone import Drone


class Simulator:
    def __init__(self, map: Map, path: Path) -> None:
        self.map = map
        self.path = path
        self.nb_drones = self.map.nb_drones
        self.hub_occ: dict[Hub, int] = {h: 0 for h in self.map.hubs}
        self.hub_occ[self.map.start_hub] = self.nb_drones

    def _snapshot(
        self, drones: list[Drone]
    ) -> tuple[dict[Hub, list[int]], set[int]]:
        """Snapshot hub -> drone_ids and in-transit drone ids."""
        snap: dict[Hub, list[int]] = {h: [] for h in self.map.hubs}
        in_transit: set[int] = set()
        for drone in drones:
            snap[drone.current_hub].append(drone.drone_id)
            if drone.in_transit:
                in_transit.add(drone.drone_id)
        return snap, in_transit

    def simulate(
        self,
    ) -> tuple[list[dict[Hub, list[int]]], list[set[int]], list[str]]:
        drones = [Drone(i + 1, self.path) for i in range(self.nb_drones)]
        turns: list[dict[Hub, list[int]]] = []
        in_transit_turns: list[set[int]] = []
        output: list[str] = []
        end = self.map.end_hub
        # Drones currently in transit to each hub (connection occupancy)
        transiting_to: dict[Hub, int] = {h: 0 for h in self.map.hubs}

        snap, in_transit = self._snapshot(drones)
        turns.append(snap)
        in_transit_turns.append(in_transit)

        while self.hub_occ.get(end, 0) < self.nb_drones:
            turn_moves: list[str] = []

            for drone in drones:
                if drone.arrived:
                    continue

                if drone.in_transit:
                    # Phase 2: complete restricted transit
                    if (next_hub := drone.next_hub) is None:
                        continue
                    if self.hub_occ.get(next_hub, 0) >= next_hub.max_drones:
                        continue  # hub still full, wait
                    transiting_to[next_hub] -= 1
                    drone.move()
                    self.hub_occ[drone.current_hub] += 1
                    move = f"D{drone.drone_id}-{drone.current_hub.name}"
                    turn_moves.append(move)
                    continue

                if (next_hub := drone.next_hub) is None:
                    continue

                if next_hub.zone_type == ZoneType.restricted:
                    # Phase 1: check connection capacity only
                    if transiting_to.get(next_hub, 0) >= 1:
                        continue  # connection occupied
                    origin = drone.current_hub.name
                    self.hub_occ[drone.current_hub] -= 1
                    transiting_to[next_hub] += 1
                    drone.move()
                    move = f"D{drone.drone_id}-{origin}-{next_hub.name}"
                    turn_moves.append(move)
                else:
                    # Normal move: check hub capacity
                    if self.hub_occ.get(next_hub, 0) >= next_hub.max_drones:
                        continue  # next hub full, drone waits
                    self.hub_occ[drone.current_hub] -= 1
                    drone.move()
                    self.hub_occ[drone.current_hub] += 1
                    move = f"D{drone.drone_id}-{drone.current_hub.name}"
                    turn_moves.append(move)

            if turn_moves:
                output.append(" ".join(turn_moves))

            snap, in_transit = self._snapshot(drones)
            turns.append(snap)
            in_transit_turns.append(in_transit)

        return turns, in_transit_turns, output
