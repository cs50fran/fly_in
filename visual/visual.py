import pygame
from models.map import Map
from models.path import Path
from models.hub import Hub

pygame.font.init()
pygame.init()

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)

# WINDOW DIMENSIONS
WIDTH, HEIGHT = 1400, 800
PADDING = 75
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fly-in")

# CONNECTIONS INFO
EDGE_COLOR = (0, 0, 0)
EDGE_SIZE = 15

# HUB SIZE — maybe adjust according to number of hubs
HUB_SIZE = 20

FPS = 60
FRAMES_PER_TURN = 60  # advance one turn per second

# DRONE INFO
DRONE_SIZE = (30, 30)
DRONE = pygame.transform.scale(pygame.image.load("assets/drone.png"), DRONE_SIZE)
DRONE = pygame.transform.rotate(DRONE, 45)
DRONE.fill(WHITE, special_flags=pygame.BLEND_RGB_MULT)

# BACKGROUND
SPACE = pygame.transform.scale(pygame.image.load("assets/space.png"), (WIDTH, HEIGHT))


class Visualizer:
    def __init__(self, map: Map, path: Path, turns: list[dict[Hub, list[int]]]) -> None:
        self.map = map
        self.turns = turns
        self.reshaped_map = self._reshape_map()
        self.current_turn = 0
        self.frame_counter = 0
        self.playing = False
        self.names_and_coords: dict[str, tuple[int, int]] = {
            hub.name: coords for hub, coords in self.reshaped_map.items()
            }


    def _reshape_map(self) -> dict[Hub, tuple[int, int]]:
        coords = [(hub.x, hub.y) for hub in self.map.hubs]

        min_x = min(coords, key=lambda c: c[0])[0]
        max_x = max(coords, key=lambda c: c[0])[0]
        min_y = min(coords, key=lambda c: c[1])[1]
        max_y = max(coords, key=lambda c: c[1])[1]

        x_scale = (WIDTH - 2 * PADDING) / ((max_x - min_x) if max_x != min_x else 1)
        y_scale = (HEIGHT - 2 * PADDING) / ((max_y - min_y) if max_y != min_y else 1)

        hub_positions: dict[Hub, tuple[int, int]] = {}
        for hub in self.map.hubs:
            x = int(PADDING + (hub.x - min_x) * x_scale)
            y = int(HEIGHT // 2 if min_y == max_y else PADDING + (hub.y - min_y) * y_scale)
            hub_positions[hub] = (x, y)

        return hub_positions

    def _draw_connections(self) -> None:
        names_and_coords: dict[str, tuple[int, int]] = {
            hub.name: coords for hub, coords in self.reshaped_map.items()
        }
        for c in self.map.connections:
            from_pos = names_and_coords[c.zone1]
            to_pos = names_and_coords[c.zone2]
            pygame.draw.line(WIN, GREY, from_pos, to_pos, 5)

    def _draw_map(self) -> None:
        for hub, pos in self.reshaped_map.items():
            color = pygame.Color(hub.color if hub.color else "white")
            pygame.draw.circle(WIN, color, pos, HUB_SIZE)

    def _drone_positions(self, turn_index: int) -> dict[int, Hub]:
        """Build a drone_id -> hub map for a given turn snapshot."""
        result: dict[int, Hub] = {}
        for hub, ids in self.turns[turn_index].items():
            for drone_id in ids:
                result[drone_id] = hub
        return result

    def _draw_drones(self, t: float) -> None:
        current_positions = self._drone_positions(self.current_turn)
        prev_positions = (
            self._drone_positions(self.current_turn - 1)
            if self.current_turn > 0
            else current_positions
        )

        for drone_id, current_hub in current_positions.items():
            prev_hub = prev_positions.get(drone_id, current_hub)

            if prev_hub == current_hub:
                # drone didn't move this turn — draw stationary
                coords = self.reshaped_map[current_hub]
                pygame.draw.circle(WIN, WHITE, coords, 5)
            else:
                # drone moved — lerp from previous hub to current hub
                start_pos = pygame.math.Vector2(self.reshaped_map[prev_hub])
                end_pos = pygame.math.Vector2(self.reshaped_map[current_hub])
                curr_pos = start_pos.lerp(end_pos, t)
                pygame.draw.circle(WIN, WHITE, curr_pos, 5)

    def _draw_window(self, t: float) -> None:
        WIN.blit(SPACE, (0, 0))
        self._draw_connections()
        self._draw_map()
        self._draw_drones(t)
        pygame.display.update()

    def run(self) -> None:
        clock = pygame.Clock()

        while True:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT and self.current_turn < len(self.turns) - 1:
                        self.current_turn += 1
                        self.frame_counter = 0
                    if event.key == pygame.K_LEFT and self.current_turn > 0:
                        self.current_turn -= 1
                        self.frame_counter = 0
                    if event.key == pygame.K_p:
                        self.playing = not self.playing
                        self.frame_counter = 0

            if self.playing:
                self.frame_counter += 1
                if self.frame_counter >= FRAMES_PER_TURN:
                    self.frame_counter = 0
                    if self.current_turn < len(self.turns) - 1:
                        self.current_turn += 1
                    else:
                        self.playing = False

            t = self.frame_counter / FRAMES_PER_TURN
            self._draw_window(t)
