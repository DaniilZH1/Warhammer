import pygame

from settings import *

cover_tiles = [
    (4, 4),
    (4, 5),
    (5, 4),
    (5, 5)
]

objective_tiles = [
    (4, 4),
    (4, 5),
    (5, 4),
    (5, 5)
]

def draw_grid(screen):

    for x in range(GRID_SIZE):

        for y in range(GRID_SIZE):

            rect = pygame.Rect(
                x * CELL_SIZE,
                y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            tile_color = WHITE

            if (x, y) in cover_tiles:
                tile_color = (120, 180, 120)

            if (x, y) in objective_tiles:
                tile_color = (220, 180, 60)

            pygame.draw.rect(
                screen,
                tile_color,
                rect
                )
            pygame.draw.rect(screen, GRAY, rect, 1)

def draw_movement_range(screen, unit):

    for x in range(GRID_SIZE):

        for y in range(GRID_SIZE):

            dist = abs(unit.x - x) + abs(unit.y - y)

            if dist <= unit.move_range:

                rect = pygame.Rect(
                    x * CELL_SIZE,
                    y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )

                surface = pygame.Surface(
                    (CELL_SIZE, CELL_SIZE),
                    pygame.SRCALPHA
                )

                surface.fill((50, 100, 255, 40))

                screen.blit(
                    surface,
                    rect.topleft
                )
def draw_attack_range(screen, unit, units):

    for target in units:

        # НЕ подсвечиваем союзников
        if target.team == unit.team:
            continue

        dist = abs(unit.x - target.x) + abs(unit.y - target.y)

        if dist <= unit.weapon.weapon_range:

            rect = pygame.Rect(
                target.x * CELL_SIZE,
                target.y * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            surface = pygame.Surface(
                (CELL_SIZE, CELL_SIZE),
                pygame.SRCALPHA
            )

            surface.fill((255, 60, 60, 120))

            screen.blit(
                surface,
                rect.topleft
            )

def is_in_cover(unit):

    return (unit.x, unit.y) in cover_tiles