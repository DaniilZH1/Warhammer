import pygame
from math import cos, pi, sin

from settings import *

# Тут рисуется поле и хранятся клетки укрытий, точек и препятствий.
board_bg = (38, 39, 35)
base_tile = (185, 181, 160)
base_tile_alt = (172, 171, 151)
cover_tile = (102, 147, 108)
objective_tile = (205, 165, 64)
blocked_tile = (61, 58, 54)
hex_outline = (82, 83, 78)
hex_highlight = (222, 218, 190)
hex_shadow = (97, 93, 83)
cover_mark = (52, 91, 58)
objective_mark = (255, 225, 118)
blocked_mark = (34, 34, 32)

cover_tiles = [
    (2, 2),
    (2, 3),
    (7, 6),
    (7, 7),
]

objective_zones = [
    {
        "name": "LEFT",
        "tiles": [
            (2, 5),
            (2, 6),
        ],
    },
    {
        "name": "CENTER",
        "tiles": [
            (4, 4),
            (4, 5),
            (5, 4),
            (5, 5),
        ],
    },
    {
        "name": "RIGHT",
        "tiles": [
            (7, 3),
            (7, 4),
        ],
    },
]

objective_tiles = []

for zone in objective_zones:
    for tile in zone["tiles"]:
        objective_tiles.append(tile)

blocked_tiles = [
    (3, 6),
    (3, 7),
    (6, 2),
    (6, 3),
]


def draw_tile_overlay(screen, x, y, color):
    # Рисуем прозрачную подсветку клетки.
    overlay = pygame.Surface((game_width, window_height), pygame.SRCALPHA)
    pygame.draw.polygon(overlay, color, hex_points(x, y))
    screen.blit(overlay, (0, 0))


def hex_center(x, y):
    # Считаем центр гекса на экране.
    center_x = hex_margin_x + hex_size + x * hex_horizontal_spacing
    center_y = (
        hex_margin_y
        + hex_height // 2
        + y * hex_vertical_spacing
        + (x % 2) * (hex_vertical_spacing // 2)
    )

    return int(center_x), int(center_y)


def hex_points(x, y):
    center_x, center_y = hex_center(x, y)
    points = []

    for index in range(6):
        point_x = int(center_x + hex_size * cos(pi / 3 * index))
        point_y = int(center_y + hex_size * sin(pi / 3 * index))
        points.append((point_x, point_y))

    return points


def scaled_hex_points(x, y, scale):
    center_x, center_y = hex_center(x, y)
    points = []

    for point_x, point_y in hex_points(x, y):
        scaled_x = int(center_x + (point_x - center_x) * scale)
        scaled_y = int(center_y + (point_y - center_y) * scale)
        points.append((scaled_x, scaled_y))

    return points


def point_in_polygon(point, polygon):
    px, py = point
    inside = False
    previous_x, previous_y = polygon[-1]

    for current_x, current_y in polygon:
        crosses_y = (current_y > py) != (previous_y > py)

        if crosses_y:
            slope_x = (
                (previous_x - current_x)
                * (py - current_y)
                / (previous_y - current_y)
                + current_x
            )

            if px < slope_x:
                inside = not inside

        previous_x, previous_y = current_x, current_y

    return inside


def pixel_to_hex(px, py):
    # Переводим координаты мыши в координаты гекса.
    if px < 0 or px >= game_width:
        return None

    best_tile = None
    best_distance = None

    for x in range(grid_size):
        for y in range(grid_size):
            center_x, center_y = hex_center(x, y)
            distance_squared = (px - center_x) ** 2 + (py - center_y) ** 2

            if best_distance is None or distance_squared < best_distance:
                best_distance = distance_squared
                best_tile = (x, y)

    if best_tile and point_in_polygon((px, py), hex_points(*best_tile)):
        return best_tile

    return None


def draw_grid(screen):
    # Рисуем все гексы поля.
    screen.fill(board_bg)

    for x in range(grid_size):
        for y in range(grid_size):
            if (x + y) % 2 == 0:
                tile_color = base_tile
            else:
                tile_color = base_tile_alt

            if (x, y) in cover_tiles:
                tile_color = cover_tile

            if (x, y) in objective_tiles:
                tile_color = objective_tile

            if (x, y) in blocked_tiles:
                tile_color = blocked_tile

            points = hex_points(x, y)
            inner_points = scaled_hex_points(x, y, 0.88)
            center_x, center_y = hex_center(x, y)

            pygame.draw.polygon(screen, tile_color, points)
            pygame.draw.polygon(screen, hex_highlight, points, 1)
            pygame.draw.polygon(screen, hex_shadow, inner_points, 1)
            pygame.draw.polygon(screen, hex_outline, points, 2)

            if (x, y) in cover_tiles:
                draw_cover_detail(screen, center_x, center_y)

            if (x, y) in blocked_tiles:
                draw_blocked_detail(screen, points)

            if (x, y) in objective_tiles:
                draw_objective_detail(screen, center_x, center_y)


def draw_cover_detail(screen, center_x, center_y):
    offsets = [
        (-18, -6),
        (-5, 12),
        (13, -3),
    ]

    for offset_x, offset_y in offsets:
        pygame.draw.circle(
            screen,
            cover_mark,
            (center_x + offset_x, center_y + offset_y),
            8,
        )
        pygame.draw.circle(
            screen,
            (130, 174, 126),
            (center_x + offset_x - 2, center_y + offset_y - 2),
            3,
        )


def draw_blocked_detail(screen, points):
    pygame.draw.polygon(screen, blocked_mark, scaled_points(points, 0.72), 0)

    for start, end in [
        (points[0], points[3]),
        (points[1], points[4]),
        (points[2], points[5]),
    ]:
        pygame.draw.line(screen, (103, 100, 94), start, end, 2)


def draw_objective_detail(screen, center_x, center_y):
    pygame.draw.circle(screen, (85, 68, 34), (center_x, center_y), 20, 3)
    pygame.draw.circle(screen, objective_mark, (center_x, center_y), 12, 2)
    pygame.draw.circle(screen, (85, 68, 34), (center_x, center_y), 4)


def scaled_points(points, scale):
    total_x = 0
    total_y = 0

    for point in points:
        total_x += point[0]
        total_y += point[1]

    center_x = total_x / len(points)
    center_y = total_y / len(points)
    scaled = []

    for point_x, point_y in points:
        scaled_x = int(center_x + (point_x - center_x) * scale)
        scaled_y = int(center_y + (point_y - center_y) * scale)
        scaled.append((scaled_x, scaled_y))

    return scaled


def objective_center(zone):
    total_x = 0
    total_y = 0

    for x, y in zone["tiles"]:
        center_x, center_y = hex_center(x, y)
        total_x += center_x
        total_y += center_y

    return (
        total_x // len(zone["tiles"]),
        total_y // len(zone["tiles"]),
    )


def draw_objective_indicators(screen, font, units):
    # Рисуем маленькую надпись над каждой точкой.
    from rules import objective_statuses

    statuses = objective_statuses(units)
    index = 0

    for zone in objective_zones:
        status = statuses[index]
        x, y = objective_center(zone)

        if status["controller"] == 1:
            label = "M"
            color = (100, 180, 255)
        elif status["controller"] == 2:
            label = "O"
            color = (100, 255, 100)
        else:
            label = "-"
            color = (210, 210, 210)

        text = font.render(f"{label} {status['marine']}:{status['ork']}", True, color)
        rect = text.get_rect(center=(x, y - hex_size // 2))
        backdrop = rect.inflate(12, 6)

        pygame.draw.rect(screen, (28, 29, 28), backdrop, border_radius=4)
        pygame.draw.rect(screen, color, backdrop, 2, border_radius=4)
        screen.blit(text, rect)
        index += 1


def draw_movement_range(screen, unit, units):
    from rules import reachable_tiles

    for x, y in reachable_tiles(unit, units):
        draw_tile_overlay(screen, x, y, (50, 100, 255, 40))


def draw_target_range(screen, unit, units, max_range, color):
    from rules import distance

    for target in units:

        if target.team == unit.team:
            continue

        dist = distance(unit.x, unit.y, target.x, target.y)

        if dist <= max_range:
            draw_tile_overlay(screen, target.x, target.y, color)


def draw_attack_range(screen, unit, units):
    from rules import can_shoot_target

    for target in units:
        if can_shoot_target(unit, target, units):
            draw_tile_overlay(screen, target.x, target.y, (255, 60, 60, 120))


def draw_invalid_targets(screen, unit, units, valid_targets):
    # Подсвечиваем врагов, которых сейчас нельзя атаковать.
    valid_target_set = set(valid_targets)

    for target in units:
        if target.team == unit.team:
            continue

        if target in valid_target_set:
            continue

        draw_tile_overlay(screen, target.x, target.y, (120, 40, 40, 45))


def is_in_cover(unit):

    return (unit.x, unit.y) in cover_tiles


def is_blocked(x, y):
    return (x, y) in blocked_tiles
