import os
import sys
from validate_map import validate_map
from solver import solver
from simulation import Simulator
from visual import Visualizer


if __name__ == "__main__":
    usage = "Usage: python fly_in.py <map_file> [--visual]"

    if len(sys.argv) not in (2, 3):
        print(usage)
        sys.exit(1)

    visual = len(sys.argv) == 3
    if visual and sys.argv[2] != "--visual":
        print(usage)
        sys.exit(1)

    map_path = sys.argv[1]
    if not os.path.isfile(map_path):
        print(f"Error: file '{map_path}' not found")
        sys.exit(1)

    try:
        map = validate_map(map_path)
        path = solver(map)
        simulator = Simulator(map, path)
        turns, in_transit_turns, output = simulator.simulate()
        for t in output:
            print(t)
        visualiser = Visualizer(map, path, turns, in_transit_turns)

        if visual:
            visualiser.run()

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
