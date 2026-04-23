*This project has been created as part of the 42 curriculum by <fdinis-d>.*

# Fly-in

## Description

Fly-in is a drone routing simulation. Given a map file describing a network of zones and connections, the program:

1. Parses and validates the map.
2. Computes an optimal path from the start zone to the end zone using Dijkstra's algorithm.
3. Simulates turn-by-turn movement of a fleet of drones along that path, respecting zone capacity, connection capacity, and restricted zone transit rules.
4. Outputs each turn's drone movements to stdout in the format `D<id>-<zone>` or `D<id>-<connection>`, if it's flying to a restricted hub.
5. Renders the simulation in a pygame graphical window.

The goal is to move all drones from the start zone to the end zone in the fewest possible simulation turns.

## Instructions

### Requirements

- Python 3.10 or later
- A virtual environment is recommended

### Installation

```bash
make install
```

Or manually:

```bash
python -m venv .fly_venv
source .fly_venv/bin/activate
pip install -r requirements.txt
```

### Running

```bash
make run                                      # default map
make run MAP=maps/medium/01_dead_end_trap.txt # specific map
make visual MAP=maps/easy/01_linear_path.txt  # with pygame visualizer
```

### Debugging

```bash
make debug MAP=maps/easy/01_linear_path.txt
```

### Linting

```bash
make lint
```

Runs `flake8` and `mypy` with the required flags.

### Tests

```bash
pytest tests/
```

Parametrized tests validate that all files in `maps/error/` raise a parsing error.

### Cleanup

```bash
make clean
```

## Algorithm

### Pathfinding — Dijkstra's algorithm

The solver (`solver.py`) implements Dijkstra's algorithm on the zone graph. Each zone has a traversal cost determined by its type:

| Zone type  | Cost   |
|------------|--------|
| normal     | 1 turn |
| priority   | 1 turn |
| restricted | 2 turns |
| blocked    | excluded from search |

Priority zones cost the same as normal zones but are preferred when two paths tie on total cost. This is implemented by storing a secondary `priority_cost` value (−1 per priority zone visited) in each heap entry, used as a tiebreaker.

Blocked zones are skipped entirely during neighbor expansion. The algorithm terminates as soon as the end zone is popped from the heap, so it never explores more of the graph than necessary.

### Simulation — turn-by-turn scheduler

The simulator (`simulation.py`) moves all drones each turn following these rules:

- **Zone capacity (`max_drones`)**: a drone may only move into a zone if the current occupancy is below the zone's limit. The start and end zones are exceptions — the start zone holds all drones initially, and multiple drones may arrive at the end zone.
- **Connection capacity (`max_link_capacity`)**: at most one drone per turn may traverse a given connection (default). Higher capacities, when configured, allow multiple drones to cross simultaneously.
- **Restricted zone transit**: moving into a restricted zone takes 2 turns. On turn 1 the drone is marked `in_transit` and occupies the connection; on turn 2 it completes the move into the zone. A drone in transit cannot be redirected or stopped.
- **Waiting**: if a drone cannot move (capacity blocked), it stays in place and retries next turn.

All drones share a single pre-computed path. The simulation ends when all drones have reached the end zone.

### Complexity

| Operation            | Complexity |
|----------------------|------------|
| Dijkstra pathfinding | O((V + E) log V) |
| Simulation per turn  | O(D) where D = number of drones |
| Total simulation     | O(D × T) where T = total turns |

## Visual Representation

The pygame visualizer (`visual.py`) renders the network and drone positions in real time. Key features:

- **Graph layout**: zone coordinates from the map file are scaled and padded to fit the window. Each zone is drawn as a labeled circle; connections are drawn as lines between them.
- **Zone coloring**: zones use the color specified in the map metadata (e.g., `color=red`). Zones without a color default to white.
- **Drone rendering**: each drone is displayed as a small icon. Drones are grouped at their current zone and animate linearly between zones as the simulation progresses.
- **Turn-by-turn playback**: the visualizer replays the simulation turn by turn. Use the arrow keys to step forward and backward through turns, or let it play automatically.
- **In-transit state**: drones crossing a restricted zone (2-turn move) are shown mid-connection during the intermediate turn, giving a clear visual indication of the delayed transit.

This makes it straightforward to verify correctness, spot bottlenecks (drones queuing at a capacity-limited zone), and understand the routing strategy at a glance.

## Resources

### References

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Priority queues in Python — `heapq` documentation](https://docs.python.org/3/library/heapq.html)
- [Graph algorithms in Python: BFS, DFS and beyond — freeCodeCamp](https://www.freecodecamp.org/news/graph-algorithms-in-python-bfs-dfs-and-beyond/)
- [Shortest path algorithm practice — 101computing.net](https://www.101computing.net/short-path-algorithm-practice/)
- [Dijkstra's algorithm playlist — YouTube](https://www.youtube.com/watch?v=sf_KeGarJkg&list=PLSVu1-lON6LyvJV6EwIJrcZi4ONJmQCQ5)
- [Dijkstra's algorithm explained — YouTube](https://www.youtube.com/watch?v=HBIoHSAsbQY&t=605s)
- [pygame-ce documentation](https://pyga.me/docs/)
- [pygame in 90 minutes — YouTube](https://www.youtube.com/watch?v=jO6qQDNa2UY&pp=ygUUcHlnYW1lIGluIDkwIG1pbnV0ZXM%3D)

### AI usage

Claude (Anthropic) was used during this project for the following tasks:

- Reviewing code for bugs and quality issues (project review).
- Helping draft this README according to the subject requirements.
- Explaining edge cases in Dijkstra's algorithm and heap-based priority handling.
- Suggesting fixes for identified bugs (reviewed and applied manually).

All generated suggestions were reviewed, tested, and understood before being incorporated. No code was copied without full comprehension.
