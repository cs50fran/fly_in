import pygame
import math
from models.map import Map
from models.path import Path
from models.hub import Hub, ZoneType

pygame.font.init()
pygame.init()

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
TURN_BAR_BG = (50, 50, 50)
PINK = (255, 48, 168)

# WINDOW DIMENSIONS
WIDTH, HEIGHT = 1400, 800
PADDING = 75
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fly-in")

# CONNECTIONS INFO
EDGE_COLOR = (200, 200, 200)
EDGE_SIZE = 15

# HUB SIZE — maybe adjust according to number of hubs
HUB_SIZE = 20

FPS = 60
FRAMES_PER_TURN = 60  # advance one turn per second

# FONTS
FONT_SMALL = pygame.font.SysFont("monospace", 12)
FONT_MEDIUM = pygame.font.SysFont("monospace", 16)
FONT_BIG = pygame.font.SysFont("monospace", 20)

# DRONE INFO
DRONE_SIZE = (30, 30)
DRONE = pygame.transform.scale(
    pygame.image.load("assets/drone.png"), DRONE_SIZE
)
DRONE = pygame.transform.rotate(DRONE, 45)
DRONE.fill(WHITE, special_flags=pygame.BLEND_RGB_MULT)

# BACKGROUND
SPACE = pygame.transform.scale(
    pygame.image.load("assets/space.png"), (WIDTH, HEIGHT)
)


# ARROWS
def draw_arrow(
    x: int,
    y: int,
    color: tuple[int, int, int],
    direction: str = "up",
) -> None:
    """Draw a small directional arrow with tip anchored at (x, y)."""
    if direction == "up":
        pygame.draw.line(WIN, color, (x, y + 14), (x, y + 2), 3)
        pygame.draw.polygon(
            WIN, color, [(x, y), (x - 6, y + 8), (x + 6, y + 8)]
        )
    elif direction == "down":
        pygame.draw.line(WIN, color, (x, y - 14), (x, y - 2), 3)
        pygame.draw.polygon(
            WIN, color, [(x, y), (x - 6, y - 8), (x + 6, y - 8)]
        )
    elif direction == "left":
        pygame.draw.line(WIN, color, (x + 14, y), (x + 2, y), 3)
        pygame.draw.polygon(
            WIN, color, [(x, y), (x + 8, y - 6), (x + 8, y + 6)]
        )
    elif direction == "right":
        pygame.draw.line(WIN, color, (x - 14, y), (x - 2, y), 3)
        pygame.draw.polygon(
            WIN, color, [(x, y), (x - 8, y - 6), (x - 8, y + 6)]
        )


class Visualizer:
    def __init__(
        self, map: Map, path: Path,
        turns: list[dict[Hub, list[int]]],
        in_transit_turns: list[set[int]]
    ) -> None:
        self.map = map
        self.turns = turns
        self.in_transit_turns = in_transit_turns
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

        x_range = (max_x - min_x) if max_x != min_x else 1
        y_range = (max_y - min_y) if max_y != min_y else 1
        x_scale = (WIDTH - 2 * PADDING) / x_range
        y_scale = (HEIGHT - 2 * PADDING) / y_range

        hub_positions: dict[Hub, tuple[int, int]] = {}
        for hub in self.map.hubs:
            x = int(PADDING + (hub.x - min_x) * x_scale)
            if min_y == max_y:
                y = HEIGHT // 2
            else:
                y = int(PADDING + (hub.y - min_y) * y_scale)
            hub_positions[hub] = (x, y)

        return hub_positions

    def _draw_connections(self) -> None:
        names_and_coords: dict[str, tuple[int, int]] = {
            hub.name: coords for hub, coords in self.reshaped_map.items()
        }
        for c in self.map.connections:
            from_pos = names_and_coords[c.zone1]
            to_pos = names_and_coords[c.zone2]
            pygame.draw.line(WIN, EDGE_COLOR, from_pos, to_pos, 5)

    def _draw_rainbow_hub(self, pos: tuple[int, int]) -> None:
        segments = 12
        arc_rect = pygame.Rect(
            pos[0] - HUB_SIZE, pos[1] - HUB_SIZE,
            HUB_SIZE * 2, HUB_SIZE * 2
        )
        for i in range(segments):
            hue = (360 / segments) * i
            c = pygame.Color(0, 0, 0)
            c.hsva = (hue, 100, 100, 100)
            start_angle = math.tau / segments * i
            stop_angle = math.tau / segments * (i + 1)
            pygame.draw.arc(
                WIN, c, arc_rect, start_angle, stop_angle, HUB_SIZE
            )

    def _draw_hubs(self) -> None:
        for hub, pos in self.reshaped_map.items():
            if hub.color == 'rainbow':
                self._draw_rainbow_hub(pos)
            else:
                color = pygame.Color(hub.color if hub.color else "white")
                if hub.zone_type == ZoneType.restricted:
                    pygame.draw.circle(WIN, ORANGE, pos, HUB_SIZE + 7, 3)
                pygame.draw.circle(WIN, color, pos, HUB_SIZE)

    def _draw_hub_names(self) -> None:
        for hub, pos in self.reshaped_map.items():
            label = FONT_SMALL.render(hub.name, True, WHITE)
            lx = pos[0] - label.get_width() // 2
            WIN.blit(label, (lx, pos[1] + HUB_SIZE + 5))

    def _draw_turn_counter(self) -> None:
        total = len(self.turns) - 1
        # While animating, show the destination turn immediately
        displayed = (
            self.current_turn + 1
            if self.frame_counter > 0 and self.current_turn < total
            else self.current_turn
        )
        label = FONT_MEDIUM.render(f"Turn {displayed} / {total}", True, WHITE)
        WIN.blit(label, (20, 12))

        bar_x, bar_y = 20, 35
        bar_w, bar_h = WIDTH - 40, 10
        fill_w = int(bar_w * (displayed / total)) if total > 0 else 0
        bg_rect = (bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(WIN, TURN_BAR_BG, bg_rect, border_radius=4)
        if fill_w > 0:
            fg_rect = (bar_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(WIN, PINK, fg_rect, border_radius=4)

    # If we could freeze the exact position would be amazing

    def _drone_positions(self, turn_index: int) -> dict[int, Hub]:
        """Build a drone_id -> hub map for a given turn snapshot."""
        result: dict[int, Hub] = {}
        for hub, ids in self.turns[turn_index].items():
            for drone_id in ids:
                result[drone_id] = hub
        return result

    def _draw_drones(self, t: float) -> None:
        # t=0: draw at current turn (static rest position)
        # t>0: lerp toward next turn (animation in progress)
        current_positions = self._drone_positions(self.current_turn)
        next_positions = (
            self._drone_positions(self.current_turn + 1)
            if self.current_turn + 1 < len(self.turns)
            else current_positions
        )
        # While animating, use destination in_transit snapshot so the drone
        # turns black when approaching a restricted hub, not when leaving.
        next_turn = self.current_turn + 1
        if self.frame_counter > 0 and next_turn < len(self.in_transit_turns):
            in_transit = self.in_transit_turns[next_turn]
        else:
            in_transit = self.in_transit_turns[self.current_turn]

        for drone_id, current_hub in current_positions.items():
            next_hub = next_positions.get(drone_id, current_hub)
            color = BLACK if drone_id in in_transit else WHITE

            if current_hub == next_hub:
                # drone doesn't move next turn — draw stationary
                coords = self.reshaped_map[current_hub]
                pygame.draw.circle(WIN, color, coords, 5)
            else:
                # drone moves next turn — lerp from current hub toward next hub
                start_pos = pygame.math.Vector2(self.reshaped_map[current_hub])
                end_pos = pygame.math.Vector2(self.reshaped_map[next_hub])
                curr_pos = start_pos.lerp(end_pos, t)
                pygame.draw.circle(WIN, color, curr_pos, 5)

    # ADD drone_counter
    def draw_drone_counter(self) -> None:
        total = self.map.nb_drones
        arrived = len(self.turns[self.current_turn].get(self.map.end_hub, []))
        label = FONT_MEDIUM.render(f"Arrived {arrived} / {total}", True, WHITE)

        # Place counter at upper-right, just below the turn progress bar.
        bar_w, bar_h = 170, 12
        bar_x, bar_y = WIDTH - bar_w - 20, 60
        label_x = bar_x + (bar_w - label.get_width()) // 2
        WIN.blit(label, (label_x, 78))

        fill_w = int(bar_w * (arrived / total)) if total > 0 else 0
        bg_rect = (bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(WIN, TURN_BAR_BG, bg_rect, border_radius=4)
        if fill_w > 0:
            fg_rect = (bar_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(WIN, PINK, fg_rect, border_radius=4)

    def draw_is_playing(self, playing: bool) -> None:
        playing_label = FONT_BIG.render("playing...", True, PINK)
        stoped_label = FONT_MEDIUM.render("press SPACEBAR", True, WHITE)
        if playing:
            label = playing_label
        else:
            label = stoped_label

        WIN.blit(label, (WIDTH - 155, 10))

    def draw_speed(self, playing: bool) -> None:
        if playing:
            up_label = FONT_MEDIUM.render(
                "Press upward arrow to increase speed", True, WHITE
            )
            base_x, base_y = WIDTH - 420, HEIGHT - 95
            draw_arrow(base_x + 10, base_y, PINK, "up")
            WIN.blit(up_label, (base_x + 24, base_y))

            down_label = FONT_MEDIUM.render(
                "Press downward arrow to decrease speed", True, WHITE
            )
            down_y = base_y + 26
            draw_arrow(base_x + 10, down_y + 20, PINK, "down")
            WIN.blit(down_label, (base_x + 24, down_y + 5))

    def draw_turn_navigation(self) -> None:
        left_label = FONT_MEDIUM.render(
            "Press left arrow to go back one turn", True, WHITE
        )
        right_label = FONT_MEDIUM.render(
            "Press right arrow to advance one turn", True, WHITE
        )
        base_x, base_y = WIDTH - 420, HEIGHT - 95

        # Left arrow icon
        draw_arrow(base_x + 4, base_y + 10, PINK, "left")
        WIN.blit(left_label, (base_x + 28, base_y))

        # Right arrow icon
        right_y = base_y + 26
        draw_arrow(base_x + 22, right_y + 10, PINK, "right")
        WIN.blit(right_label, (base_x + 28, right_y + 1))

    def _draw_window(self, t: float, playing: bool) -> None:
        WIN.blit(SPACE, (0, 0))
        self._draw_connections()
        self._draw_hubs()
        self._draw_hub_names()
        self._draw_drones(t)
        self._draw_turn_counter()
        self.draw_drone_counter()
        self.draw_is_playing(playing)
        if playing:
            self.draw_speed(playing)
        else:
            self.draw_turn_navigation()
        pygame.display.update()

    def run(self) -> None:
        clock = pygame.Clock()
        speed = 1

        while True:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    at_end = self.current_turn >= len(self.turns) - 1
                    if event.key == pygame.K_RIGHT and not at_end:
                        self.current_turn += 1
                        self.frame_counter = 0
                    if event.key == pygame.K_LEFT and self.current_turn > 0:
                        self.current_turn -= 1
                        self.frame_counter = 0
                    if event.key == pygame.K_SPACE:
                        self.playing = not self.playing
                        self.frame_counter = 0
                    if event.key == pygame.K_UP and self.playing:
                        if speed < 4:
                            speed += 1
                    if event.key == pygame.K_DOWN and self.playing:
                        if speed > 1:
                            speed -= 1

            if self.playing:
                self.frame_counter += speed
                if self.frame_counter >= FRAMES_PER_TURN:
                    self.frame_counter = 0
                    if self.current_turn < len(self.turns) - 1:
                        self.current_turn += 1
                    else:
                        self.playing = False

            t = self.frame_counter / FRAMES_PER_TURN
            self._draw_window(t, self.playing)
