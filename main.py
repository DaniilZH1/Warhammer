import pygame
import sys

from settings import *
from unit import Unit
from combat import (
    attack,
    hit_chance,
    wound_chance,
    save_chance,
    dice_log,
    dice_to_symbol
)
from board import (
    draw_grid,
    draw_movement_range,
    draw_attack_range
)
from turn_manager import next_turn

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Warhammer")

font = pygame.font.SysFont(None, 28)

clock = pygame.time.Clock()

units = [
    Unit(1, 1, 1),
    Unit(1, 3, 1),

    Unit(8, 8, 2),
    Unit(8, 6, 2)
]

selected_unit = None
hovered_target = None
current_team = 1

def get_unit_at(x, y):

    for unit in units:

        if unit.x == x and unit.y == y:
            return unit

    return None

def distance(x1, y1, x2, y2):

    return abs(x1 - x2) + abs(y1 - y2)

running = True

while running:

    screen.fill(BLACK)

    draw_grid(screen)

    mx, my = pygame.mouse.get_pos()

    hover_x = mx // CELL_SIZE
    hover_y = my // CELL_SIZE

    hovered_target = get_unit_at(
        hover_x,
        hover_y
    )

    if selected_unit:
        draw_movement_range(
            screen,
            selected_unit
        )

        draw_attack_range(
            screen,
            selected_unit,
            units
        )

    # UI PANEL
    pygame.draw.rect(
        screen,
        (40, 40, 40),
        (GAME_WIDTH, 0, UI_WIDTH, HEIGHT)
    )

    # DRAW UNITS
    for unit in units:

        is_selected = unit == selected_unit

        is_hovered = unit == hovered_target

        unit.draw(
            screen,
            font,
            selected=is_selected,
            hovered=is_hovered
        )

    # UNIT STATS
    if selected_unit:

        stats = [
            f"MODELS: {selected_unit.models}",
            f"HP: {selected_unit.hp}",
            f"TGH: {selected_unit.toughness}",
            f"SAVE: {selected_unit.armor_save}+",
            "",
            f"WEAPON: {selected_unit.weapon.name}",
            f"ATK: {selected_unit.weapon.attacks}",
            f"STR: {selected_unit.weapon.strength}",
            f"AP: {selected_unit.weapon.ap}",
            f"DMG: {selected_unit.weapon.damage}",
            f"RANGE: {selected_unit.weapon.weapon_range}"
        ]

        for i, stat in enumerate(stats):

            text = font.render(
                stat,
                True,
                WHITE
            )

            screen.blit(
                text,
                (GAME_WIDTH + 20, 50 + i * 40)
            )
    
     # TARGET PREVIEW
    if (
    selected_unit
    and hovered_target
    and hovered_target.team != selected_unit.team
    ):

        hit = hit_chance(
            selected_unit.ballistic_skill
        )

        wound = wound_chance(
            selected_unit.weapon.strength,
            hovered_target.toughness
        )

        save = save_chance(
            hovered_target.armor_save
        )

        pygame.draw.line(
            screen,
            (100, 100, 100),
            (GAME_WIDTH + 10, 470),
            (WIDTH - 10, 470),
            2
        )

        preview = [
            "TARGET",
            "",
            f"HIT: {hit}%",
            f"WOUND: {wound}%",
            f"SAVE: {save}%",
            "",
            f"DMG: {selected_unit.weapon.damage}"
        ]

        for i, line in enumerate(preview):

            text = font.render(
                line,
                True,
                (255, 220, 100)
            )

            screen.blit(
                text,
                ( GAME_WIDTH + 20, 500 + i * 35 )
            )

     # DICE LOG
    dice_y = 760

    title = font.render(
        "DICE",
        True,
        (255, 255, 255)
    )

    screen.blit(
        title,
        (GAME_WIDTH + 20, dice_y)
    )

    for i, (roll_type, value) in enumerate(dice_log):

        dice_text = font.render(
            f"{roll_type}: {dice_to_symbol(value)}",
            True,
            (255, 255, 255)
        )

        screen.blit(
            dice_text,
            (GAME_WIDTH + 20, dice_y + 40 + i * 30)
        )

    pygame.display.flip()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            mx, my = pygame.mouse.get_pos()

            grid_x = mx // CELL_SIZE
            grid_y = my // CELL_SIZE

            clicked_unit = get_unit_at(grid_x, grid_y)

            # SELECT UNIT
            if clicked_unit and clicked_unit.team == current_team:

                if not clicked_unit.has_acted:
                    selected_unit = clicked_unit

            # ACTION
            elif selected_unit:

                dist = distance(
                    selected_unit.x,
                    selected_unit.y,
                    grid_x,
                    grid_y
                )

                target = get_unit_at(grid_x, grid_y)

                # ATTACK
                if target and target.team != current_team:

                    if dist <= selected_unit.weapon.weapon_range:

                        attack(selected_unit, target)

                        selected_unit.has_acted = True

                        if target.models <= 0:

                            if target in units:
                                units.remove(target)

                        selected_unit = None

                # MOVE
                elif not target:

                    if dist <= selected_unit.move_range:

                        selected_unit.x = grid_x
                        selected_unit.y = grid_y

                        selected_unit.has_acted = True

                        selected_unit = None

                # END TURN
                team_done = all(
                    unit.has_acted
                    for unit in units
                    if unit.team == current_team
                )

                if team_done:

                    current_team = next_turn(
                        current_team,
                        units
                    )

    clock.tick(60)

pygame.quit()
sys.exit()