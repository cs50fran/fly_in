# Map Reference

## File Format

```
nb_drones: <positive integer>

start_hub: <name> <x> <y> [metadata]
end_hub:   <name> <x> <y> [metadata]
hub:       <name> <x> <y> [metadata]

connection: <zone1>-<zone2> [metadata]
```

- Comments start with `#` and are ignored
- Zone names: no dashes, no spaces
- Coordinates are always integers
- Exactly one `start_hub` and one `end_hub`

---

## Hub

| Field        | Type   | Default  | Notes                          |
|--------------|--------|----------|--------------------------------|
| name         | str    | required | unique, no dashes/spaces       |
| x, y         | int    | required |                                |
| zone         | str    | normal   | normal, blocked, restricted, priority |
| color        | str    | none     | any single-word string         |
| max_drones   | int    | 1        | must be positive integer       |

### Zone types

| Type       | Move cost | Notes                              |
|------------|-----------|------------------------------------|
| normal     | 1 turn    |                                    |
| blocked    | —         | inaccessible, cannot be entered    |
| restricted | 2 turns   | drone occupies connection in transit, must arrive next turn |
| priority   | 1 turn    | preferred in pathfinding           |

---

## Connection

| Field            | Type | Default | Notes                              |
|------------------|------|---------|------------------------------------|
| zone1, zone2     | str  | required| must reference already-defined zones |
| max_link_capacity| int  | 1       | max drones traversing simultaneously |

- Bidirectional (a-b == b-a, no duplicates)

---

## Validation Rules

- First line must be `nb_drones: <positive integer>`
- Exactly one `start_hub`, one `end_hub`
- Each zone name must be unique
- Zone type must be one of the four valid types
- Capacity values must be positive integers
- Connections reference only already-defined zones
- No duplicate connections
- On error: stop and report line number + cause
