import os
import sys
from parser.validate_maps import validate_map


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python fly_in.py <map_file>")
        sys.exit(1)

    map_path = sys.argv[1]

    if not os.path.isfile(map_path):
        print(f"Error: file '{map_path}' not found")
        sys.exit(1)

    try:
        result = validate_map(map_path)
        print(result)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
