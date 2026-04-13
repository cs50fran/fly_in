# validate_map(map) -> bool:

    # first line must be nb_drones: <positive integer>

    # must have exactly one start_hub and one end_hub

    # each zone must have a unique name (no dashes, no spaces)
    # each zone must have valid integer coordinates

    # zone type must be one of: normal, blocked, restricted, priority
    # capacity values (max_drones, max_link_capacity) must be positive integers

    # connections must reference only already-defined zones
    # no duplicate connections (a-b and b-a are the same)

    # on any error: stop and report line number + cause


"""
receive map_path which in fly_in.py will be sys.arg[3] or something
here we assume is good
validation of path later in main
"""

from models.map import Map
from models.hub import Hub, ZoneType
from models.connection import Connection

valid_keys = {
    "nb_drones",
    "start_hub",
    "end_hub",
    "hub",
    "connection"
}

valid_hub_keys = {
    "start_hub",
    "end_hub",
    "hub",
}

valid_meta_types = {
    'color',
    'zone',
    'max_drones'
}



def validate_and_build_hub(
        values: str,
        is_start: bool = False,
        is_end: bool = False
    ) -> Hub:
    parts = values.split(maxsplit=3)

    if len(parts) == 3:
        name, x, y = parts
        return Hub(name=name, x=int(x), y=int(y), is_start=is_start, is_end=is_end)
    elif len(parts) == 4:
        name, x, y, meta = parts
    else:
        raise ValueError(
            "Incorrect formatting for Hub data"
        )

    if not (meta.startswith('[')) or not (meta.endswith(']')):
        raise ValueError(
            "Incorrect Metadata formatting - should be in []"
        )
    meta = meta.strip('[]')

    meta_data: list[list[str]] = []
    seen_meta_types: set[str] = set()
    for item in meta.split():
        meta_type, sep, meta_value = item.partition('=')
        if not sep or sep != '=':
            raise ValueError(
                "Incorrect Metadata formatting - expecting 'meta=value'"
            )
        if meta_type not in valid_meta_types:
            raise ValueError(
                f"Incorrect Metadata type - must be in {valid_meta_types}"
            )
        if meta_type in seen_meta_types:
            raise ValueError(
                f"Duplicate metadata tag '{meta_type}'"
            )
        seen_meta_types.add(meta_type)
        meta_data.append([meta_type, meta_value])

    color: str | None = None
    max_drones: int = 1
    zone: ZoneType = ZoneType.normal

    # nao verifica duplicados
    for data in meta_data:
        if data[0] == 'color':
            color = data[1]
        elif data[0] == 'max_drones':
            max_drones = int(data[1])
        elif data[0] == "zone":
            zone = ZoneType(data[1])

    return Hub(
        name=name, x=int(x), y=int(y), zone_type=zone,
        color=color, max_drones=max_drones,
        is_start=is_start, is_end=is_end
        )


def validate_and_build_connection(
        values: str,
        known_hubs: list[str],
    ) -> Connection:
    parts = values.split()

    if len(parts) == 1:
        raw_zones = parts[0]
        max_link_capacity = 1
    elif len(parts) == 2:
        raw_zones, meta = parts
        if not (meta.startswith('[')) or not (meta.endswith(']')):
            raise ValueError(
                "Incorrect Metadata formatting - should be in []"
            )
        meta = meta.strip('[]')
        key, sep, val = meta.partition('=')
        if not sep or key != 'max_link_capacity':
            raise ValueError(
                "Connection metadata must be [max_link_capacity=<int>]"
            )
        max_link_capacity = int(val)
    else:
        raise ValueError(
            "Incorrect formatting for Connection data"
        )

    if '-' not in raw_zones:
        raise ValueError(
            f"Connection must be in format zone1-zone2, got: '{raw_zones}'"
        )
    zone1, _, zone2 = raw_zones.partition('-')

    if zone1 not in known_hubs:
        raise ValueError(f"Unknown hub '{zone1}' in connection")
    if zone2 not in known_hubs:
        raise ValueError(f"Unknown hub '{zone2}' in connection")

    return Connection(zone1=zone1, zone2=zone2, max_link_capacity=max_link_capacity)


def validate_map(map_path: str) -> Map:
    nb_drones: int | None = None
    hubs: list[Hub] = []
    connections: list[Connection] = []
    seen_coords: set[tuple[int, int]] = set()
    seen_hub_names: set[str] = set()
    seen_connections: set[frozenset[str]] = set()
    first_real_line = True

    with open(map_path, 'r') as f:
        for line_no, line in enumerate(f, start=1):
            line = line.split('#')[0].strip()
            if not line:
                continue

            key, sep, values = line.partition(':')
            if not sep:
                raise ValueError(
                    f"  Malformed line: '{line}', line: {line_no}"
                    "\n  Expected format: KEY:VALUE"
                )

            key = key.strip()
            if key not in valid_keys:
                raise ValueError(
                    f"  Invalid key: '{key}', line: {line_no}"
                    f"\n  Must be one of {valid_keys}"
                )

            if key == "nb_drones":
                if not first_real_line:
                    raise ValueError(
                        f"  'nb_drones' must be the first line, line: {line_no}"
                    )
                if nb_drones is not None:
                    raise ValueError(
                        f"  'nb_drones' defined more than once, line: {line_no}"
                    )
                try:
                    nb_drones = int(values.strip())
                except ValueError:
                    raise ValueError(
                        f"  line {line_no}: 'nb_drones' must be a valid integer"
                    )
                if nb_drones < 1:
                    raise ValueError(
                        f"  line {line_no}: 'nb_drones' must be a positive integer, got {nb_drones}"
                    )

            elif key in valid_hub_keys:
                try:
                    if key == "start_hub":
                        new_hub = validate_and_build_hub(values.strip(), is_start=True)
                    elif key == "end_hub":
                        new_hub = validate_and_build_hub(values.strip(), is_end=True)
                    else:
                        new_hub = validate_and_build_hub(values.strip())
                except ValueError as e:
                    raise ValueError(f"  line {line_no}: {e}") from e

                if new_hub.name in seen_hub_names:
                    raise ValueError(
                        f"  Duplicate hub name '{new_hub.name}', line: {line_no}"
                    )
                coords = (new_hub.x, new_hub.y)
                if coords in seen_coords:
                    raise ValueError(
                        f"  Duplicate hub coordinates {coords}, line: {line_no}"
                    )
                seen_hub_names.add(new_hub.name)
                seen_coords.add(coords)
                hubs.append(new_hub)

            elif key == 'connection':
                known_hub_names = [h.name for h in hubs]
                try:
                    new_conn = validate_and_build_connection(values.strip(), known_hub_names)
                except ValueError as e:
                    raise ValueError(f"  line {line_no}: {e}") from e
                conn_key = frozenset([new_conn.zone1, new_conn.zone2])
                if conn_key in seen_connections:
                    raise ValueError(
                        f"  Duplicate connection '{new_conn.zone1}-{new_conn.zone2}', line: {line_no}"
                    )
                seen_connections.add(conn_key)
                connections.append(new_conn)

            first_real_line = False

    if nb_drones is None:
        raise ValueError("  Missing 'nb_drones' definition")

    start_count = sum(1 for h in hubs if h.is_start)
    end_count = sum(1 for h in hubs if h.is_end)
    if start_count != 1:
        raise ValueError(f"  Expected exactly one start_hub, found {start_count}")
    if end_count != 1:
        raise ValueError(f"  Expected exactly one end_hub, found {end_count}")

    return Map(nb_drones=nb_drones, hubs=hubs, connections=connections)
            

            




