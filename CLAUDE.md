# Fly-In — Claude Context

## Project Purpose

Multi-agent drone pathfinding and simulation on a graph-based map. The system parses a map file, finds an optimal path with Dijkstra's algorithm, simulates turn-by-turn drone movement with capacity and transit constraints, and renders the result in a pygame visualization.

## Pipeline

```
fly_in.py <map_file>
  → validate_map()     # parser/validate_maps.py
  → solver()           # solver/solver.py
  → Simulator.simulate()  # turns/simulation.py
  → game()             # visual/visual.py
```

## Tech Stack

- Python 3
- `pydantic >= 2.0` — data validation for all models
- `pygame-ce >= 2.4` — visualization
- `pytest` — tests (parametrized error-map validation)
- `flake8`, `mypy` — linting and type checking

## Project Structure

```
fly_in.py               # entry point
models/
  hub.py                # Hub (zone node): zone_type, max_drones, coordinates
  connection.py         # Connection (edge): bidirectional, max_link_capacity
  drone.py              # Drone: path_index, in_transit, arrived, move()
  map.py                # Map: hubs + connections + metadata
  path.py               # Path: ordered list of hubs start → end
parser/
  validate_maps.py      # map file parser + validator → Map
solver/
  solver.py             # Dijkstra pathfinding → Path
turns/
  simulation.py         # turn-by-turn simulator → turns snapshot list
visual/
  visual.py             # pygame renderer
maps/
  easy / medium / hard / challenger / error
tests/
  test_parser_errors.py # validates all maps/error/* raise exceptions
assets/
  drone.png, space.png
```

## Zone Types

| Type       | Cost   | Notes                                              |
|------------|--------|----------------------------------------------------|
| normal     | 1 turn |                                                    |
| blocked    | —      | inaccessible, excluded from pathfinding            |
| restricted | 2 turns| drone occupies hub for 2 turns (in_transit flag)   |
| priority   | 1 turn | preferred by pathfinder (priority_cost = -1)       |

## Key Mechanics

- **Hub capacity** (`max_drones`): drones queue and wait if hub is full.
- **Restricted zone transit**: 2-turn move — turn 1 marks `in_transit`, turn 2 completes the move.
- **Connection capacity** (`max_link_capacity`): defined in the model but not yet enforced in the simulator.
- **Single path**: Dijkstra computes one path shared by all drones (no dynamic rerouting).

## Running

```bash
python -m venv fly_venv && source fly_venv/bin/activate
pip install -r requirements.txt
python fly_in.py maps/easy/01_linear_path.txt
```

## Tests

```bash
pytest tests/
```

Tests parametrize over every file in `maps/error/` and assert each raises `ValueError` or `Exception`.

## Map File Format

```
nb_drones: <int>
start_hub: <name> <x> <y> [zone=<type>] [color=<name>] [max_drones=<int>]
end_hub:   <name> <x> <y> [...]
hub:       <name> <x> <y> [...]
connection: <zone1>-<zone2> [max_link_capacity=<int>]
```

- Comments start with `#`
- Zone names: no dashes, no spaces
- Coordinates: integers, must be unique
- Bidirectional connections (a-b == b-a)
- See `MAP.md` for full validation rules

## Guidelines

- Always read the relevant code files before making suggestions or debugging. Never assume what the code does — inspect it first.
- When the user asks about files or directories, assume they mean the local project filesystem unless explicitly stated otherwise.
- Keep solutions simple. Avoid over-engineered answers with unnecessary imports or advanced patterns. Start minimal and elaborate only if asked.
- After making changes to any `.py` file, run it to verify it works. Do not assume correctness — test it.
- When debugging, never ask the user to check or read the code themselves. Read the relevant files, trace the problem, and present the diagnosis and fix directly. The user reports symptoms — Claude finds the cause.

## Context

- This is a learning-oriented project (42 school curriculum). Explanations should build from simple to complex.
- The user actively pushes back on wrong assumptions — read the code first, always.
