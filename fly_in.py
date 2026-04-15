import os
import sys
from parser.validate_maps import validate_map
from solver.solver import solver
from turns.simulation import Simulator


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python fly_in.py <map_file>")
        sys.exit(1)

    map_path = sys.argv[1]

    if not os.path.isfile(map_path):
        print(f"Error: file '{map_path}' not found")
        sys.exit(1)

    try:
        map = validate_map(map_path)
        path = solver(map)
        simulator = Simulator(map, path)
        turns, output = simulator.simulate()
        for t in turns:
            print("\n".join(
                f"{hub.name}:[{', '.join(f'D{d.drone_id}' for d in drones)}]"
                for hub, drones in t.items()
            ))
            print("-----")
        print(f"Turns: {len(turns)}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
