from heapq import heappop, heappush

from models.map import Map
from models.hub import Hub, ZoneType
from models.path import Path


def solver(map: Map) -> Path:

    start = map.start_hub
    end = map.end_hub

    pq = [(0, 0, start.name, start)]  # initializes pq
    visited: set[Hub] = set()
    came_from: dict[Hub, Hub] = {}
    cost_so_far: dict[Hub, int] = {start: 0}  # pyright: ignore

    while pq:
        cost, priority_cost, _, current_hub = heappop(pq)
        if current_hub in visited:
            continue
        visited.add(current_hub)
        if current_hub == end:
            break

        for n in map.get_neighbours(current_hub):
            if n in visited:
                continue
            if n.zone_type == ZoneType.blocked:
                continue
            new_cost = cost + n.get_cost()
            if new_cost < cost_so_far.get(n, float('inf')):
                cost_so_far[n] = new_cost
                priority_cost = -1 if n.zone_type == ZoneType.priority else 0
                came_from[n] = current_hub
                heappush(pq, (new_cost, priority_cost, n.name, n))

    if end not in came_from:
        raise ValueError("No path found from start to end")
    path = []
    current = end
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()

    return Path(hubs=path)
