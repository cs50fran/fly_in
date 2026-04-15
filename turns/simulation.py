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
        self.hub_occ[self.map.start_hub] = self.nb_drones  # all drones start here

    def simulate(self) -> tuple[list[dict[Hub, list[Drone]]], list[str]]:
        drones = [Drone(i + 1, self.path) for i in range(self.nb_drones)]
        turns: list[dict[Hub, list[Drone]]] = []
        output: list[str] = []
        start = self.map.start_hub
        end = self.map.end_hub

        #  1st snapshot, b4 movement
        initial: dict[Hub, list[Drone]] = {h: [] for h in self.map.hubs}
        initial[start] = list(drones)
        turns.append(initial)
        
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
                    f"D{drone.drone_id}-{self.path.hubs[drone.path_index].name}"
                )
                if not drone.in_transit:
                    self.hub_occ[drone.current_hub] += 1

            if turn_moves:
                output.append(" ".join(turn_moves))

            # snapshot: hub -> list of drones currently there
            snapshot: dict[Hub, list[Drone]] = {h: [] for h in self.map.hubs}
            for drone in drones:
                if not drone.arrived:
                    snapshot[drone.current_hub].append(drone)
                snapshot[end] = [d for d in drones if d.arrived]
            turns.append(snapshot)

        return turns, output
