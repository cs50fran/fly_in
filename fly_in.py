import os
import sys
from validate_maps import validate_map
from solver import solver
from simulation import Simulator
from visual import Visualizer


if __name__ == "__main__":
    visual = False
    if len(sys.argv) < 2:
        print("Usage: python fly_in.py <map_file>")
        sys.exit(1)
    elif len(sys.argv) == 3:
        visual = False
        if sys.argv[2] == "--visual":
            visual = True
        else:
            print("Usage: python fly_in.py <map_file> (--visual)")
            sys.exit(1)

    elif len(sys.argv) > 3:
        print("Usage: python fly_in.py <map_file> (--visual)")
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
