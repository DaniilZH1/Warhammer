import pygame
import sys

from settings import *
from unit import Unit
from combat import (
    attack,
    attempt_charge,
    combat_log,
    dice_log,
    dice_to_symbol,
    hit_chance,
    is_engaged,
    log_event,
    melee_attack,
    save_chance,
    wound_chance,
)
from board import (
    draw_attack_range,
    draw_grid,
    draw_movement_range,
    objective_tiles,
)
from turn_manager import next_turn

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Warhammer")

font = pygame.font.SysFont(None, 28)
small_font = pygame.font.SysFont(None, 22)
clock = pygame.time.Clock()

NEXT_PHASE_RECT = pygame.Rect(GAME_WIDTH + 20, 92, 160, 32)
WAAAGH_RECT = pygame.Rect(GAME_WIDTH + 20, 130, 160, 32)
VICTORY_POINTS = 5


def create_units():
    return [
        Unit(1, 1, 1, "marines"),
        Unit(1, 3, 1, "marines"),
        Unit(8, 8, 2, "orks"),
        Unit(8, 6, 2, "orks"),
    ]


units = create_units()

selected_unit = None
hovered_target = None
current_team = 1
marine_vp = 0
ork_vp = 0
winner = None

phases = [
    "MOVEMENT",
    "SHOOTING",
    "CHARGE",
    "FIGHT",
]

current_phase_index = 0
current_phase = phases[current_phase_index]
waaagh_active = False
waaagh_used = False


def reset_game():
    global units, selected_unit, hovered_target, current_team
    global marine_vp, ork_vp, current_phase_index, current_phase
    global waaagh_active, waaagh_used, winner

    units = create_units()
    selected_unit = None
    hovered_target = None
    current_team = 1
    marine_vp = 0
    ork_vp = 0
    current_phase_index = 0
    current_phase = phases[current_phase_index]
    waaagh_active = False
    waaagh_used = False
    winner = None
    combat_log.clear()
    dice_log.clear()
    log_event("NEW GAME")


def draw_ui_line(text, x, y, color=WHITE):
    text = str(text)

    if len(text) > 18:
        text = text[:15] + "..."

    screen.blit(
        small_font.render(text, True, color),
        (x, y),
    )


def draw_button(rect, label, enabled=True):
    fill = (70, 70, 70) if enabled else (45, 45, 45)
    outline = (160, 160, 160) if enabled else (90, 90, 90)
    text_color = WHITE if enabled else (140, 140, 140)

    pygame.draw.rect(screen, fill, rect, border_radius=4)
    pygame.draw.rect(screen, outline, rect, 1, border_radius=4)

    text = small_font.render(label, True, text_color)
    screen.blit(
        text,
        (
            rect.centerx - text.get_width() // 2,
            rect.centery - text.get_height() // 2,
        ),
    )


def get_unit_at(x, y):
    for unit in units:
        if unit.x == x and unit.y == y:
            return unit

    return None


def distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def count_objective_control(team):
    total = 0

    for unit in units:
        if unit.team != team:
            continue

        if (unit.x, unit.y) in objective_tiles:
            total += unit.models

    return total


def remove_dead_units():
    for unit in units[:]:
        if unit.hp <= 0 or unit.models <= 0:
            units.remove(unit)


def check_victory():
    global winner

    teams_alive = {unit.team for unit in units}

    if len(teams_alive) == 1:
        winner = teams_alive.pop()
        log_event(f"TEAM {winner} WINS!")
        return

    if marine_vp >= VICTORY_POINTS:
        winner = 1
        log_event("MARINES WIN BY VP!")
    elif ork_vp >= VICTORY_POINTS:
        winner = 2
        log_event("ORKS WIN BY VP!")


def unit_can_act(unit):
    return unit.ap > 0


def mark_phase_action(unit):

    if unit.ap <= 0:
        unit.has_acted = True


def score_objectives():
    global marine_vp, ork_vp

    marine_control = count_objective_control(1)
    ork_control = count_objective_control(2)

    if marine_control > ork_control:
        marine_vp += 1
        log_event("SPACE MARINES SCORE 1 VP!")
    elif ork_control > marine_control:
        ork_vp += 1
        log_event("ORKS SCORE 1 VP!")

    check_victory()


def advance_phase():
    global current_phase, current_phase_index, current_team
    global selected_unit, waaagh_active

    selected_unit = None

    if winner:
        return

    if current_phase == "FIGHT":
        score_objectives()
        current_phase_index = 0
        current_team = next_turn(current_team, units)
        waaagh_active = False
    else:
        current_phase_index += 1

    current_phase = phases[current_phase_index]
    log_event(f"PHASE: {current_phase}")


def activate_waaagh():
    global waaagh_active, waaagh_used

    if current_team != 2:
        log_event("ONLY ORKS CAN WAAAGH!")
        return

    if waaagh_used:
        log_event("WAAAGH ALREADY USED!")
        return

    waaagh_active = True
    waaagh_used = True
    log_event("WAAAAAGH!!!")


def draw_sidebar():
    pygame.draw.rect(
        screen,
        (40, 40, 40),
        (GAME_WIDTH, 0, UI_WIDTH, HEIGHT),
    )

    draw_ui_line(
        f"VP M:{marine_vp} O:{ork_vp}/{VICTORY_POINTS}",
        GAME_WIDTH + 20,
        15,
        (255, 220, 100),
    )

    draw_ui_line(
        f"TEAM {current_team}",
        GAME_WIDTH + 20,
        42,
        WHITE,
    )

    draw_ui_line(
        current_phase,
        GAME_WIDTH + 20,
        65,
        (255, 220, 100),
    )

    draw_button(NEXT_PHASE_RECT, "NEXT PHASE", enabled=winner is None)
    draw_button(
        WAAAGH_RECT,
        "WAAAGH",
        enabled=winner is None and current_team == 2 and not waaagh_used,
    )

    if winner:
        winner_name = "MARINES" if winner == 1 else "ORKS"
        stats = [
            f"{winner_name} WIN",
            "",
            "PRESS R",
            "TO RESTART",
        ]
    elif selected_unit:
        stats = [
            selected_unit.faction.upper(),
            f"MODELS: {selected_unit.models}",
            f"HP: {selected_unit.hp}",
            f"TGH: {selected_unit.toughness}",
            f"SAVE: {selected_unit.armor_save}+",
            f"AP: {selected_unit.ap}/{selected_unit.max_ap}"
            "",
            selected_unit.weapon.name.upper(),
            f"ATK: {selected_unit.weapon.attacks}",
            f"STR: {selected_unit.weapon.strength}",
            f"AP: {selected_unit.weapon.ap}",
            f"DMG: {selected_unit.weapon.damage}",
            f"RANGE: {selected_unit.weapon.weapon_range}",
        ]
    else:
        stats = [
            "SELECT UNIT",
            "",
            "ENTER/NEXT",
            "ADVANCES PHASE",
        ]

    for i, stat in enumerate(stats):
        draw_ui_line(
            stat,
            GAME_WIDTH + 20,
            178 + i * 22,
            WHITE,
        )


def draw_target_preview():
    if (
        not selected_unit
        or not hovered_target
        or hovered_target.team == selected_unit.team
    ):
        return

    hit = hit_chance(selected_unit.ballistic_skill)
    wound = wound_chance(
        selected_unit.weapon.strength,
        hovered_target.toughness,
    )
    save = save_chance(hovered_target.armor_save)

    pygame.draw.line(
        screen,
        (100, 100, 100),
        (GAME_WIDTH + 10, 430),
        (WIDTH - 10, 430),
        2,
    )

    preview = [
        "TARGET",
        hovered_target.faction.upper(),
        f"HIT: {hit}%",
        f"WOUND: {wound}%",
        f"SAVE: {save}%",
        f"DMG: {selected_unit.weapon.damage}",
    ]

    for i, line in enumerate(preview):
        draw_ui_line(
            line,
            GAME_WIDTH + 20,
            455 + i * 22,
            (255, 220, 100),
        )


def draw_combat_log():
    log_y = 602

    draw_ui_line("LOG", GAME_WIDTH + 20, log_y, WHITE)

    for i, line in enumerate(combat_log[-6:]):
        draw_ui_line(
            line,
            GAME_WIDTH + 20,
            log_y + 25 + i * 22,
            (210, 210, 210),
        )


def draw_dice_log():
    dice_y = 760

    draw_ui_line("DICE", GAME_WIDTH + 20, dice_y, WHITE)

    for i, (roll_type, value) in enumerate(dice_log[-2:]):
        draw_ui_line(
            f"{roll_type}: {dice_to_symbol(value)}",
            GAME_WIDTH + 20,
            dice_y + 25 + i * 22,
            WHITE,
        )


def draw_turn_header():
    if winner:
        winner_name = "SPACE MARINES" if winner == 1 else "ORKS"
        screen.blit(
            font.render(f"{winner_name} WIN!", True, (255, 220, 100)),
            (20, 20),
        )
        screen.blit(
            font.render("PRESS R TO RESTART", True, WHITE),
            (20, 60),
        )
        return

    if current_team == 1:
        turn_text = "SPACE MARINES TURN"
        turn_color = (100, 180, 255)
    else:
        turn_text = "ORKS TURN"
        turn_color = (100, 255, 100)

    screen.blit(font.render(turn_text, True, turn_color), (20, 20))
    screen.blit(
        font.render(f"PHASE: {current_phase}", True, (255, 220, 100)),
        (20, 60),
    )

    if waaagh_active:
        screen.blit(
            font.render("WAAAGH ACTIVE", True, (100, 255, 100)),
            (20, 100),
        )


def handle_board_click(grid_x, grid_y):
    global selected_unit

    if winner:
        return

    clicked_unit = get_unit_at(grid_x, grid_y)

    if clicked_unit and clicked_unit.team == current_team:
        if unit_can_act(clicked_unit):
            selected_unit = clicked_unit
        else:
            log_event("UNIT ALREADY ACTED")

        return

    if not selected_unit:
        return
    
    if selected_unit.ap <= 0:

        log_event("NO AP LEFT!")

        return

    dist = distance(
        selected_unit.x,
        selected_unit.y,
        grid_x,
        grid_y,
    )

    target = clicked_unit

    if current_phase == "MOVEMENT":
        if target:
            return

        if dist > selected_unit.move_range:
            log_event("MOVE TOO FAR!")
            return

        selected_unit.x = grid_x
        selected_unit.y = grid_y

        selected_unit.ap -= 1
        selected_unit.ap = max(0, selected_unit.ap)

        mark_phase_action(selected_unit)

        if selected_unit.ap <= 0:
            selected_unit = None
        return

    if not target or target.team == current_team:
        return

    if current_phase == "SHOOTING":
        if is_engaged(selected_unit, units):
            log_event("UNIT ENGAGED IN MELEE!")
            return

        if dist > selected_unit.weapon.weapon_range:
            log_event("TARGET OUT OF RANGE!")
            return

        attack(
            selected_unit,
            target,
            waaagh=waaagh_active,
        )

        selected_unit.ap -= 1
        selected_unit.ap = max(0, selected_unit.ap)

        mark_phase_action(selected_unit)

        if selected_unit.ap <= 0:
            selected_unit = None
        return

    if current_phase == "CHARGE":
        if attempt_charge(selected_unit, target):

            selected_unit.ap -= 2

            mark_phase_action(selected_unit)
            selected_unit = None
        return

    if current_phase == "FIGHT":
        if dist > 1:
            log_event("TARGET NOT IN MELEE RANGE!")
            return

        melee_attack(selected_unit, target)
        selected_unit.ap -= 1
        selected_unit.ap = max(0, selected_unit.ap)

        mark_phase_action(selected_unit)

        remove_dead_units()
        check_victory()
        if selected_unit.ap <= 0:
            selected_unit = None


running = True

while running:
    screen.fill(BLACK)
    draw_grid(screen)

    mx, my = pygame.mouse.get_pos()
    hover_x = mx // CELL_SIZE
    hover_y = my // CELL_SIZE
    hovered_target = get_unit_at(hover_x, hover_y)

    if selected_unit:
        if current_phase == "MOVEMENT":
            draw_movement_range(screen, selected_unit)
        elif current_phase == "SHOOTING":
            draw_attack_range(screen, selected_unit, units)

    for unit in units:
        unit.draw(
            screen,
            font,
            selected=unit == selected_unit,
            hovered=unit == hovered_target,
            engaged=is_engaged(unit, units),
        )

    draw_sidebar()
    draw_target_preview()
    draw_combat_log()
    draw_dice_log()
    draw_turn_header()

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()
            elif event.key == pygame.K_RETURN:
                advance_phase()
            elif event.key == pygame.K_SPACE:
                activate_waaagh()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if winner:
                continue

            if NEXT_PHASE_RECT.collidepoint(event.pos):
                advance_phase()
                continue

            if WAAAGH_RECT.collidepoint(event.pos):
                activate_waaagh()
                continue

            if event.pos[0] >= GAME_WIDTH:
                continue

            handle_board_click(
                event.pos[0] // CELL_SIZE,
                event.pos[1] // CELL_SIZE,
            )

    clock.tick(60)

pygame.quit()
sys.exit()
