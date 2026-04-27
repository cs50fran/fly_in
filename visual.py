import pygame
import math
import random
from collections import deque
from models.map import Map
from models.path import Path
from models.hub import Hub, ZoneType

pygame.font.init()
pygame.init()

# ── Palette ────────────────────────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PINK = (255, 48, 168)
CYAN = (0, 220, 255)
ORANGE = (255, 165, 30)
GOLD = (255, 210, 50)
GREEN = (50, 255, 130)
PURPLE = (180, 50, 255)
DIM = (50, 60, 90)
BAR_BG = (25, 30, 55)

ZONE_GLOW = {
    ZoneType.normal: (90, 150, 255),
    ZoneType.restricted: (255, 140, 30),
    ZoneType.priority: (70, 255, 150),
    ZoneType.blocked: (50, 55, 80),
}

# ── Window ─────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1400, 800
PADDING = 90
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fly-in")

HUB_SIZE = 22
FPS = 60
FRAMES_PER_TURN = 60
TRAIL_LENGTH = 20

# ── Fonts ───────────────────────────────────────────────────────────────────
FONT_TINY = pygame.font.SysFont("monospace", 10)
FONT_SMALL = pygame.font.SysFont("monospace", 12)
FONT_MEDIUM = pygame.font.SysFont("monospace", 15)
FONT_BIG = pygame.font.SysFont("monospace", 20)
FONT_TITLE = pygame.font.SysFont("monospace", 22, bold=True)

# ── Assets ──────────────────────────────────────────────────────────────────
_drone_raw = pygame.image.load("assets/drone.png")
DRONE_BASE = pygame.transform.scale(_drone_raw, (28, 28))
DRONE_BASE = pygame.transform.rotate(DRONE_BASE, 45)

SPACE = pygame.transform.scale(
    pygame.image.load("assets/space.png"), (WIDTH, HEIGHT)
)


# ── Glow cache + helpers ─────────────────────────────────────────────────────
_glow_cache: dict = {}


def _build_glow(color: tuple[int, int, int], radius: int, alpha: int) -> pygame.Surface:
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        ratio = r / radius
        a = int(alpha * (1.0 - ratio) ** 1.8)
        pygame.draw.circle(surf, (*color, a), (radius, radius), r)
    return surf


def _get_glow(
    color: tuple[int, int, int], radius: int, alpha: int = 160
) -> pygame.Surface:
    key = (color, radius, alpha)
    if key not in _glow_cache:
        _glow_cache[key] = _build_glow(color, radius, alpha)
    return _glow_cache[key]


def blit_glow(
    target: pygame.Surface,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    radius: int,
    alpha: int = 160,
) -> None:
    surf = _get_glow(color, radius, alpha)
    target.blit(surf, (pos[0] - radius, pos[1] - radius),
                special_flags=pygame.BLEND_RGBA_ADD)


def draw_panel(
    surface: pygame.Surface,
    rect: tuple[int, int, int, int],
    radius: int = 8,
    bg: tuple[int, int, int] = (8, 10, 24),
    alpha: int = 195,
) -> None:
    x, y, w, h = rect
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*bg, alpha), (0, 0, w, h), border_radius=radius)
    pygame.draw.rect(panel, (*CYAN, 45), (0, 0, w, h), 1, border_radius=radius)
    surface.blit(panel, (x, y))


# ── Particle ────────────────────────────────────────────────────────────────
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        size: float = 3.0,
        speed: float = 1.5,
    ) -> None:
        self.x = x
        self.y = y
        angle = random.uniform(0, math.tau)
        spd = random.uniform(0.3, speed)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.life = random.randint(20, 55)
        self.max_life = self.life
        self.color = color
        self.size = max(0.5, size + random.uniform(-0.5, 1.0))

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.93
        self.vy *= 0.93
        self.life -= 1
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        ratio = self.life / self.max_life
        a = int(220 * ratio)
        sz = max(1, int(self.size * ratio))
        buf = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(buf, (*self.color, a), (sz + 1, sz + 1), sz)
        surface.blit(buf, (int(self.x) - sz - 1, int(self.y) - sz - 1))


# ── Ring (shockwave) ─────────────────────────────────────────────────────────
class Ring:
    __slots__ = ("x", "y", "color", "max_r", "life", "max_life", "width")

    def __init__(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        max_r: int = 90,
        life: int = 45,
        width: int = 2,
    ) -> None:
        self.x, self.y = x, y
        self.color = color
        self.max_r = max_r
        self.life = life
        self.max_life = life
        self.width = width

    def update(self) -> bool:
        self.life -= 1
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        ratio = 1.0 - self.life / self.max_life
        r = int(self.max_r * ratio)
        a = int(200 * self.life / self.max_life)
        if r < 2:
            return
        rs = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(rs, (*self.color, a), (r + 2, r + 2), r, self.width)
        surface.blit(rs, (int(self.x) - r - 2, int(self.y) - r - 2))


# ── Star field ───────────────────────────────────────────────────────────────
class Star:
    __slots__ = ("x", "y", "speed", "size", "brightness", "phase")

    def __init__(self) -> None:
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.speed = random.uniform(0.04, 0.22)
        self.size = random.choices([1, 2], weights=[5, 1])[0]
        self.brightness = random.randint(100, 240)
        self.phase = random.uniform(0, math.tau)

    def update(self) -> None:
        self.x -= self.speed
        if self.x < 0:
            self.x = float(WIDTH)
            self.y = random.uniform(0, HEIGHT)

    def draw(self, surface: pygame.Surface, tick: int) -> None:
        pulse = 0.5 + 0.5 * math.sin(self.phase + tick * 0.03)
        b = int(self.brightness * (0.65 + 0.35 * pulse))
        if self.size == 1:
            surface.set_at((int(self.x), int(self.y)), (b, b, b))
        else:
            pygame.draw.circle(surface, (b, b, min(b + 40, 255)),
                               (int(self.x), int(self.y)), self.size)


# ── Visualizer ───────────────────────────────────────────────────────────────
class Visualizer:
    def __init__(
        self,
        map: Map,
        path: Path,
        turns: list[dict[Hub, list[int]]],
        in_transit_turns: list[set[int]],
    ) -> None:
        self.map = map
        self.path = path
        self.turns = turns
        self.in_transit_turns = in_transit_turns
        self.reshaped_map = self._reshape_map()
        self.current_turn = 0
        self.frame_counter = 0
        self.playing = False
        self.tick = 0

        self.names_and_coords: dict[str, tuple[int, int]] = {
            hub.name: coords for hub, coords in self.reshaped_map.items()
        }

        self.path_edges: set[frozenset] = set()
        ph = path.hubs
        for i in range(len(ph) - 1):
            self.path_edges.add(frozenset({ph[i].name, ph[i + 1].name}))

        self.particles: list[Particle] = []
        self.stars: list[Star] = [Star() for _ in range(180)]
        self._prev_arrived: int = 0
        self._drone_angles: dict[int, float] = {}
        self._rings: list[Ring] = []
        self._drone_history: dict[int, deque] = {}

        # Lightning
        self._lightning_cache: dict[frozenset, list[list[tuple[int, int]]]] = {}
        self._lightning_timer: int = 0
        self._lightning_surf: pygame.Surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Active edge flare
        self._active_edges: set[frozenset] = set()

        # Impact flash
        self._flash_alpha: int = 0

        # Speed lines
        self._speed_surf: pygame.Surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._speed_phase: float = 0.0

        # Scanlines (built once)
        self._scanline_surf: pygame.Surface = self._build_scanlines()

        # Mission complete
        self._mission_complete: bool = False
        self._mission_complete_tick: int = 0
        _mfont = pygame.font.SysFont("monospace", 64, bold=True)
        self._mission_label: pygame.Surface = _mfont.render("MISSION COMPLETE", True, GOLD)
        self._mission_glow: pygame.Surface = _mfont.render("MISSION COMPLETE", True, PINK)

    # ── Map reshape ───────────────────────────────────────────────────────
    def _reshape_map(self) -> dict[Hub, tuple[int, int]]:
        coords = [(hub.x, hub.y) for hub in self.map.hubs]
        min_x = min(c[0] for c in coords)
        max_x = max(c[0] for c in coords)
        min_y = min(c[1] for c in coords)
        max_y = max(c[1] for c in coords)

        x_range = (max_x - min_x) or 1
        y_range = (max_y - min_y) or 1
        x_scale = (WIDTH - 2 * PADDING) / x_range
        y_scale = (HEIGHT - 2 * PADDING) / y_range

        result: dict[Hub, tuple[int, int]] = {}
        for hub in self.map.hubs:
            x = int(PADDING + (hub.x - min_x) * x_scale)
            y = (HEIGHT // 2
                 if min_y == max_y
                 else int(PADDING + (hub.y - min_y) * y_scale))
            result[hub] = (x, y)
        return result

    # ── Scanlines ─────────────────────────────────────────────────────────
    def _build_scanlines(self) -> pygame.Surface:
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 3):
            pygame.draw.line(surf, (0, 0, 0, 38), (0, y), (WIDTH, y))
        return surf

    def _draw_scanlines(self) -> None:
        WIN.blit(self._scanline_surf, (0, 0))

    # ── Flash ─────────────────────────────────────────────────────────────
    def _draw_flash(self) -> None:
        if self._flash_alpha <= 0:
            return
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((220, 160, 255, self._flash_alpha))
        WIN.blit(flash, (0, 0))
        self._flash_alpha = max(0, self._flash_alpha - 11)

    # ── Background ────────────────────────────────────────────────────────
    def _draw_background(self) -> None:
        WIN.blit(SPACE, (0, 0))
        for star in self.stars:
            star.update()
            star.draw(WIN, self.tick)

    # ── Lightning helpers ─────────────────────────────────────────────────
    def _build_lightning(self, p1: tuple, p2: tuple, segs: int = 8) -> list[list[tuple[int, int]]]:
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = math.hypot(dx, dy) or 1
        px, py = -dy / length, dx / length

        def make_bolt() -> list[tuple[int, int]]:
            pts = [p1]
            for i in range(1, segs):
                t = i / segs
                bx = p1[0] + dx * t
                by = p1[1] + dy * t
                off = random.gauss(0, length * 0.07)
                pts.append((int(bx + px * off), int(by + py * off)))
            pts.append(p2)
            return pts

        return [make_bolt(), make_bolt()]

    def _draw_lightning_on(self, surf: pygame.Surface, pts: list[tuple[int, int]], color: tuple, alpha: int) -> None:
        for i in range(len(pts) - 1):
            pygame.draw.line(surf, (*color, alpha), pts[i], pts[i + 1], 1)

    # ── Active edge pre-pass ──────────────────────────────────────────────
    def _compute_active_edges(self, t: float) -> None:
        if t <= 0:
            self._active_edges = set()
            return
        current_pos = self._drone_positions(self.current_turn)
        next_pos = (
            self._drone_positions(self.current_turn + 1)
            if self.current_turn + 1 < len(self.turns)
            else current_pos
        )
        self._active_edges = set()
        for drone_id, curr_hub in current_pos.items():
            next_hub = next_pos.get(drone_id, curr_hub)
            if curr_hub != next_hub:
                self._active_edges.add(frozenset({curr_hub.name, next_hub.name}))

    # ── Connections ───────────────────────────────────────────────────────
    def _draw_connections(self) -> None:
        flow = (self.tick * 2) % 60
        refresh = self._lightning_timer % 5 == 0
        self._lightning_timer += 1

        self._lightning_surf.fill((0, 0, 0, 0))

        for c in self.map.connections:
            p1 = self.names_and_coords[c.zone1]
            p2 = self.names_and_coords[c.zone2]
            key = frozenset({c.zone1, c.zone2})
            on_path = key in self.path_edges
            active = key in self._active_edges

            if on_path:
                # Active edge flare — blaze white when a drone traverses it
                if active:
                    pygame.draw.line(WIN, (255, 255, 220), p1, p2, 6)
                    mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
                    blit_glow(WIN, WHITE, mid, 40, 140)

                # Deep glow track
                pygame.draw.line(WIN, (10, 50, 90), p1, p2, 10)
                pygame.draw.line(WIN, (15, 80, 140), p1, p2, 6)
                pygame.draw.line(WIN, CYAN, p1, p2, 2)

                # Flowing energy dots
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                length = math.hypot(dx, dy)
                if length > 0:
                    ux, uy = dx / length, dy / length
                    for d in range(0, int(length), 24):
                        offset = (d + flow) % length
                        fpx = int(p1[0] + ux * offset)
                        fpy = int(p1[1] + uy * offset)
                        fade = math.sin(math.pi * offset / length)
                        a = int(200 * fade)
                        dot = pygame.Surface((8, 8), pygame.SRCALPHA)
                        pygame.draw.circle(dot, (*CYAN, a), (4, 4), 4)
                        WIN.blit(dot, (fpx - 4, fpy - 4))

                # Lightning arcs
                if refresh or key not in self._lightning_cache:
                    self._lightning_cache[key] = self._build_lightning(p1, p2)
                bolts = self._lightning_cache[key]
                pulse_a = int(110 + 60 * math.sin(self.tick * 0.22))
                for bolt in bolts:
                    self._draw_lightning_on(self._lightning_surf, bolt, CYAN, pulse_a)
                    self._draw_lightning_on(self._lightning_surf, bolt, (180, 240, 255), pulse_a // 2)
            else:
                pygame.draw.line(WIN, (45, 55, 85), p1, p2, 3)

        WIN.blit(self._lightning_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # ── Hubs ──────────────────────────────────────────────────────────────
    def _drone_count_at(self, hub: Hub) -> int:
        return len(self.turns[self.current_turn].get(hub, []))

    def _draw_rainbow_hub(self, pos: tuple[int, int], pulse: float) -> None:
        segments = 18
        r = int(HUB_SIZE + 3 + 4 * pulse)
        arc_rect = pygame.Rect(pos[0] - r, pos[1] - r, r * 2, r * 2)
        for i in range(segments):
            hue = ((360 / segments) * i + self.tick * 2) % 360
            c = pygame.Color(0, 0, 0)
            c.hsva = (hue, 100, 100, 100)
            start_a = math.tau / segments * i
            stop_a = math.tau / segments * (i + 1)
            pygame.draw.arc(WIN, c, arc_rect, start_a, stop_a, r)

    def _draw_hubs(self) -> None:
        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.07)

        for hub, pos in self.reshaped_map.items():
            n = self._drone_count_at(hub)
            zc = ZONE_GLOW[hub.zone_type]

            # Outer ambient glow — brightens with drone occupancy
            glow_r = HUB_SIZE + 20 + int(8 * pulse)
            glow_a = 55 + int(35 * pulse) + min(n * 18, 85)
            blit_glow(WIN, zc, pos, glow_r, glow_a)

            if hub.color == "rainbow":
                self._draw_rainbow_hub(pos, pulse)
            else:
                if hub.color:
                    bc = pygame.Color(hub.color)
                    fill = (bc.r, bc.g, bc.b)
                else:
                    fill = zc

                # Zone-specific rings
                if hub.zone_type == ZoneType.restricted:
                    rr = HUB_SIZE + 7 + int(4 * pulse)
                    pygame.draw.circle(WIN, ORANGE, pos, rr, 3)
                    blit_glow(WIN, ORANGE, pos, rr + 8, 50)

                elif hub.zone_type == ZoneType.priority:
                    rr = HUB_SIZE + 6
                    pygame.draw.circle(WIN, GOLD, pos, rr, 2)
                    blit_glow(WIN, GOLD, pos, rr + 10, 65)

                # Body
                pygame.draw.circle(WIN, fill, pos, HUB_SIZE)

                # Specular highlight
                if hub.zone_type != ZoneType.blocked:
                    hi = (pos[0] - HUB_SIZE // 3, pos[1] - HUB_SIZE // 3)
                    hisurf = pygame.Surface((HUB_SIZE, HUB_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(hisurf, (255, 255, 255, 90),
                                       (HUB_SIZE // 2, HUB_SIZE // 2),
                                       HUB_SIZE // 3)
                    WIN.blit(hisurf, (hi[0] - HUB_SIZE // 2, hi[1] - HUB_SIZE // 2))

                # Border
                border = tuple(min(255, v + 55) for v in fill[:3])
                pygame.draw.circle(WIN, border, pos, HUB_SIZE, 2)

            # Overcrowding alarm — red pulsing ring + jitter when at capacity
            if hub.max_drones > 0 and n >= hub.max_drones:
                wp = 0.5 + 0.5 * math.sin(self.tick * 0.35)
                wr = HUB_SIZE + 12 + int(6 * wp)
                wa = int(80 + 90 * wp)
                pygame.draw.circle(WIN, (255, 40, 40), pos, wr, 3)
                blit_glow(WIN, (255, 40, 40), pos, wr + 12, wa)
                jpos = (pos[0] + random.randint(-2, 2), pos[1] + random.randint(-2, 2))
                pygame.draw.circle(WIN, (255, 100, 100), jpos, wr + 5, 1)

            # Start / end label + extra glow
            if hub == self.map.start_hub:
                blit_glow(WIN, GREEN, pos, HUB_SIZE + 28, 75)
                lbl = FONT_TINY.render("START", True, GREEN)
                WIN.blit(lbl, (pos[0] - lbl.get_width() // 2,
                               pos[1] - HUB_SIZE - 20))

            elif hub == self.map.end_hub:
                blit_glow(WIN, PINK, pos, HUB_SIZE + 28, 75)
                lbl = FONT_TINY.render("END", True, PINK)
                WIN.blit(lbl, (pos[0] - lbl.get_width() // 2,
                               pos[1] - HUB_SIZE - 20))

    def _draw_hub_names(self) -> None:
        for hub, pos in self.reshaped_map.items():
            label = FONT_SMALL.render(hub.name, True, (175, 195, 235))
            lx = pos[0] - label.get_width() // 2
            WIN.blit(label, (lx, pos[1] + HUB_SIZE + 8))

    # ── Speed lines ───────────────────────────────────────────────────────
    def _draw_speed_lines(self, speed: int) -> None:
        if speed < 3:
            return
        self._speed_phase = (self._speed_phase + speed * 0.9) % 360
        cx, cy = WIDTH // 2, HEIGHT // 2
        self._speed_surf.fill((0, 0, 0, 0))
        n_lines = 60
        spread = (speed - 2) * 100
        for i in range(n_lines):
            angle = math.radians(360 / n_lines * i + self._speed_phase)
            inner = random.uniform(55, 110)
            outer = inner + random.uniform(30, spread)
            a = random.randint(20, 75)
            x1 = int(cx + math.cos(angle) * inner)
            y1 = int(cy + math.sin(angle) * inner)
            x2 = int(cx + math.cos(angle) * outer)
            y2 = int(cy + math.sin(angle) * outer)
            pygame.draw.line(self._speed_surf, (*WHITE, a), (x1, y1), (x2, y2), 1)
        WIN.blit(self._speed_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    # ── Drones ────────────────────────────────────────────────────────────
    def _drone_positions(self, turn_index: int) -> dict[int, Hub]:
        result: dict[int, Hub] = {}
        for hub, ids in self.turns[turn_index].items():
            for drone_id in ids:
                result[drone_id] = hub
        return result

    def _draw_warp_trail(self, drone_id: int, current_pos: tuple[float, float], trail_surf: pygame.Surface) -> None:
        hist = self._drone_history.get(drone_id)
        if not hist or len(hist) < 2:
            return
        pts = list(hist) + [current_pos]
        n = len(pts)
        for i in range(1, n):
            ratio = i / n
            a = int(200 * ratio)
            w = max(1, int(5 * ratio))
            r = int(80 * (1 - ratio) + 180 * ratio)
            g = int(220 * ratio)
            b = 255
            if i > 1:
                p_prev = pts[i - 1]
                pygame.draw.line(trail_surf, (r, g, b, a // 2),
                                 (int(p_prev[0]), int(p_prev[1])),
                                 (int(pts[i][0]), int(pts[i][1])), w)
            pygame.draw.circle(trail_surf, (r, g, b, a),
                                (int(pts[i][0]), int(pts[i][1])), w)

    def _draw_drones(self, t: float) -> None:
        current_pos = self._drone_positions(self.current_turn)
        next_pos = (
            self._drone_positions(self.current_turn + 1)
            if self.current_turn + 1 < len(self.turns)
            else current_pos
        )

        next_turn = self.current_turn + 1
        if self.frame_counter > 0 and next_turn < len(self.in_transit_turns):
            in_transit = self.in_transit_turns[next_turn]
        else:
            in_transit = self.in_transit_turns[self.current_turn]

        # Arrival burst + rings + flash
        arrived_now = len(self.turns[self.current_turn].get(self.map.end_hub, []))
        if arrived_now > self._prev_arrived:
            ep = self.names_and_coords[self.map.end_hub.name]
            for _ in range(35):
                self.particles.append(Particle(ep[0], ep[1], PINK, 4, 3.5))
                self.particles.append(Particle(ep[0], ep[1], GOLD, 3, 2.5))
                self.particles.append(Particle(ep[0], ep[1], WHITE, 2, 2.0))
            for max_r, color in [(70, PINK), (110, CYAN), (150, GOLD)]:
                self._rings.append(Ring(ep[0], ep[1], color, max_r=max_r, life=50))
            self._flash_alpha = min(180, self._flash_alpha + 90)

            # Mission complete trigger
            if not self._mission_complete and arrived_now >= self.map.nb_drones:
                self._mission_complete = True
                self._mission_complete_tick = self.tick
                self._flash_alpha = 200
                for i, color in enumerate([WHITE, PINK, CYAN, GOLD, PURPLE]):
                    self._rings.append(Ring(ep[0], ep[1], color,
                                            max_r=160 + i * 45, life=75, width=3))

        self._prev_arrived = arrived_now

        trail_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        drone_draws = []

        for drone_id, curr_hub in current_pos.items():
            next_hub = next_pos.get(drone_id, curr_hub)
            is_transit = drone_id in in_transit
            moving = curr_hub != next_hub

            sv = pygame.math.Vector2(self.reshaped_map[curr_hub])
            ev = pygame.math.Vector2(self.reshaped_map[next_hub])
            pv = sv.lerp(ev, t) if moving else sv

            if drone_id not in self._drone_history:
                self._drone_history[drone_id] = deque(maxlen=TRAIL_LENGTH)
            if moving:
                self._drone_history[drone_id].append((pv.x, pv.y))

            self._draw_warp_trail(drone_id, (pv.x, pv.y), trail_surf)
            drone_draws.append((drone_id, pv, sv, ev, is_transit, moving))

        WIN.blit(trail_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        for drone_id, pv, sv, ev, is_transit, moving in drone_draws:
            if moving and t > 0 and random.random() < 0.45:
                col = ORANGE if is_transit else CYAN
                self.particles.append(Particle(pv.x, pv.y, col, 2.5, 0.9))

            gc = ORANGE if is_transit else CYAN
            blit_glow(WIN, gc, (int(pv.x), int(pv.y)), 24, 130)

            if moving:
                dx = ev.x - sv.x
                dy = ev.y - sv.y
                angle = -math.degrees(math.atan2(dy, dx))
                self._drone_angles[drone_id] = angle
            angle = self._drone_angles.get(drone_id, 0.0)

            sprite = pygame.transform.rotate(DRONE_BASE, angle)
            if is_transit:
                sprite = sprite.copy()
                sprite.fill((200, 80, 0), special_flags=pygame.BLEND_RGB_ADD)

            ipos = (int(pv.x) - sprite.get_width() // 2,
                    int(pv.y) - sprite.get_height() // 2)
            WIN.blit(sprite, ipos)

    # ── Particles ─────────────────────────────────────────────────────────
    def _update_and_draw_particles(self) -> None:
        self.particles = [p for p in self.particles if p.update()]
        for p in self.particles:
            p.draw(WIN)

    # ── Rings ─────────────────────────────────────────────────────────────
    def _update_and_draw_rings(self) -> None:
        self._rings = [r for r in self._rings if r.update()]
        for r in self._rings:
            r.draw(WIN)

    # ── Mission complete ──────────────────────────────────────────────────
    def _draw_mission_complete(self) -> None:
        if not self._mission_complete:
            return
        age = self.tick - self._mission_complete_tick

        # Continuous celebration from end hub
        if age % 10 == 0:
            ep = self.names_and_coords[self.map.end_hub.name]
            for color in [PINK, CYAN, GOLD, GREEN, PURPLE]:
                self._rings.append(Ring(
                    ep[0] + random.gauss(0, 28),
                    ep[1] + random.gauss(0, 28),
                    color,
                    max_r=random.randint(50, 130),
                    life=45,
                ))
            for _ in range(8):
                self.particles.append(
                    Particle(ep[0], ep[1], random.choice([PINK, GOLD, CYAN, WHITE]), 4, 5.0)
                )

        # Text slide-in from top, cubic ease-out
        slide_t = min(1.0, age / 45)
        ease = 1.0 - (1.0 - slide_t) ** 3
        lbl_h = self._mission_label.get_height()
        lbl_w = self._mission_label.get_width()
        target_y = HEIGHT // 2 - lbl_h // 2
        y = int(-lbl_h + (target_y + lbl_h) * ease)
        x = WIDTH // 2 - lbl_w // 2
        alpha = int(255 * ease)

        glow_pulse = 0.6 + 0.4 * math.sin(self.tick * 0.12)
        glow = self._mission_glow.copy()
        glow.set_alpha(int(alpha * 0.45 * glow_pulse))
        WIN.blit(glow, (x - 5, y - 5))
        WIN.blit(glow, (x + 5, y + 5))

        lbl = self._mission_label.copy()
        lbl.set_alpha(alpha)
        WIN.blit(lbl, (x, y))

    # ── HUD ───────────────────────────────────────────────────────────────
    def _draw_turn_bar(self) -> None:
        total = len(self.turns) - 1
        displayed = (
            self.current_turn + 1
            if self.frame_counter > 0 and self.current_turn < total
            else self.current_turn
        )

        draw_panel(WIN, (10, 6, WIDTH - 20, 50), radius=8)

        label = FONT_TITLE.render(f"TURN  {displayed:03d} / {total:03d}", True, WHITE)
        WIN.blit(label, (20, 12))

        bar_x, bar_y = 20, 42
        bar_w, bar_h = WIDTH - 40, 7
        fill_w = int(bar_w * displayed / total) if total > 0 else 0

        pygame.draw.rect(WIN, BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        if fill_w > 0:
            pygame.draw.rect(WIN, PINK, (bar_x, bar_y, fill_w, bar_h), border_radius=3)
            blit_glow(WIN, PINK, (bar_x + fill_w, bar_y + bar_h // 2), 10, 120)

    def _draw_drone_counter(self) -> None:
        total = self.map.nb_drones
        arrived = len(self.turns[self.current_turn].get(self.map.end_hub, []))
        in_flight = sum(
            len(ids)
            for hub, ids in self.turns[self.current_turn].items()
            if hub != self.map.end_hub
        )

        pw, ph = 210, 88
        px, py = WIDTH - pw - 10, 60
        draw_panel(WIN, (px, py, pw, ph))

        title = FONT_TINY.render("DRONES", True, (130, 155, 200))
        WIN.blit(title, (px + 10, py + 8))

        arr_lbl = FONT_MEDIUM.render(f"Arrived  {arrived:>3}", True, GREEN)
        fly_lbl = FONT_MEDIUM.render(f"In flight {in_flight:>3}", True, CYAN)
        total_lbl = FONT_MEDIUM.render(f"Total    {total:>3}", True, (160, 170, 210))

        WIN.blit(arr_lbl, (px + 10, py + 22))
        WIN.blit(fly_lbl, (px + 10, py + 42))
        WIN.blit(total_lbl, (px + 10, py + 62))

        bar_x = px + 10
        bar_y = py + ph - 12
        bar_w = pw - 20
        fill_w = int(bar_w * arrived / total) if total > 0 else 0
        pygame.draw.rect(WIN, BAR_BG, (bar_x, bar_y, bar_w, 5), border_radius=3)
        if fill_w > 0:
            pygame.draw.rect(WIN, GREEN, (bar_x, bar_y, fill_w, 5), border_radius=3)

    def _draw_controls(self, playing: bool, speed: int) -> None:
        if playing:
            lines = [
                (f"SPD x{speed}", "UP/DN to change"),
                ("SPACE", "pause"),
            ]
        else:
            lines = [
                ("LEFT / RIGHT", "step turns"),
                ("SPACE", "play"),
            ]

        pw = 220
        ph = 14 + len(lines) * 22
        px = WIDTH - pw - 10
        py = HEIGHT - ph - 12
        draw_panel(WIN, (px, py, pw, ph), radius=6)

        for i, (key, desc) in enumerate(lines):
            kl = FONT_SMALL.render(key, True, CYAN)
            dl = FONT_SMALL.render(desc, True, (160, 170, 210))
            WIN.blit(kl, (px + 10, py + 8 + i * 22))
            WIN.blit(dl, (px + pw // 2, py + 8 + i * 22))

        if playing:
            pulse = 0.6 + 0.4 * math.sin(self.tick * 0.18)
            col = tuple(int(v * pulse) for v in PINK)
            state_lbl = FONT_BIG.render("> PLAYING", True, col)
        else:
            state_lbl = FONT_MEDIUM.render("|| PAUSED", True, (150, 155, 195))
        WIN.blit(state_lbl, (
            WIDTH - state_lbl.get_width() - 14,
            py - state_lbl.get_height() - 8
        ))

    # ── Main frame ────────────────────────────────────────────────────────
    def _draw_window(self, t: float, playing: bool, speed: int) -> None:
        self._compute_active_edges(t)
        self._draw_background()
        self._draw_connections()
        self._draw_hubs()
        self._draw_hub_names()
        self._draw_speed_lines(speed)
        self._draw_drones(t)
        self._update_and_draw_rings()
        self._update_and_draw_particles()
        self._draw_mission_complete()
        self._draw_flash()
        self._draw_turn_bar()
        self._draw_drone_counter()
        self._draw_controls(playing, speed)
        self._draw_scanlines()
        pygame.display.update()

    def run(self) -> None:
        clock = pygame.Clock()
        speed = 1

        while True:
            clock.tick(FPS)
            self.tick += 1

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
                    if event.key == pygame.K_UP and self.playing and speed < 4:
                        speed += 1
                    if event.key == pygame.K_DOWN and self.playing and speed > 1:
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
            self._draw_window(t, self.playing, speed)
