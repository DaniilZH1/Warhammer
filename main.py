import pygame
import sys

# импорт ботов
from ai import ai_take_turn_step
from app_settings import load_app_settings, save_app_settings
from board import (
    draw_attack_range,
    draw_grid,
    draw_invalid_targets,
    draw_movement_range,
    draw_objective_indicators,
    draw_target_range,
    pixel_to_hex,
)

#импорт боевки и эффектов
from combat import attack, is_engaged, log_event, melee_attack, set_dice_delay
from effects import (
    add_damage_text,
    add_melee_effect,
    add_shot_effect,
    draw_effects,
    draw_floating_texts,
    update_effects,
    update_floating_texts,
)
from game_state import ai_turn_delay_ms, charge_max_range, GameState
from localization import role_label
from rules import (
    action_hint,
    can_charge_target,
    can_fight_target,
    can_move_to,
    can_shoot_target,
    current_action_cost,
    distance,
    get_unit_at,
    ready_units,
    unit_action_status,
    unit_can_act,
)
from settings import *
from ui import (
    next_phase_rect,
    waaagh_rect,
    draw_combat_log,
    draw_dice_log,
    draw_full_log_overlay,
    draw_help_overlay,
    draw_pause_menu,
    draw_sidebar,
    draw_start_screen,
    draw_target_preview,
    draw_turn_header,
    draw_victory_screen,
    get_sidebar_roster_unit_at,
)

pygame.init()

# отображение
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption(f"Мини Warhammer v{version}")

# Окно и шрифты создаются один раз. Arial выбран, чтобы кириллица в интерфейсе
font = pygame.font.SysFont("arial", 28)
small_font = pygame.font.SysFont("arial", 22)
clock = pygame.time.Clock()

app_settings = load_app_settings()
set_dice_delay(app_settings["dice_delay_ms"])
state = GameState(ai_orks_enabled=app_settings["ai_orks_enabled"])

#  оболочка приложения
start_screen_visible = True
pause_menu_visible = False


def persist_ai_setting():
    app_settings["ai_orks_enabled"] = state.ai_orks_enabled
    save_app_settings(app_settings)


def persist_dice_delay():
    save_app_settings(app_settings)

# Ограничение задержки кубиков
def adjust_dice_delay(delta):
    
    app_settings["dice_delay_ms"] = app_settings["dice_delay_ms"] + delta

    if app_settings["dice_delay_ms"] < 0:
        app_settings["dice_delay_ms"] = 0

    if app_settings["dice_delay_ms"] > 500:
        app_settings["dice_delay_ms"] = 500

    set_dice_delay(app_settings["dice_delay_ms"])
    persist_dice_delay()
    log_event(f"Задержка кубиков: {app_settings['dice_delay_ms']} мс")


def reset_game():
    state.reset(ai_orks_enabled=state.ai_orks_enabled)


def toggle_ai():
    state.ai_orks_enabled = not state.ai_orks_enabled
    persist_ai_setting()

    if state.ai_orks_enabled:
        ai_text = "Вкл"
    else:
        ai_text = "Выкл"

    log_event(f"AI орков: {ai_text}")


def unit_name(unit):
    return role_label(unit.role)


def log_damage_result(target, before_hp):
    
    damage = before_hp - target.hp

    if damage < 0:
        damage = 0

    if damage > 0:
        log_event(f"{unit_name(target)} Получает {damage} Урн")
    else:
        log_event("Без Урона")

    return damage


def select_next_ready_unit(previous_unit=None):
    state.selected_unit = None

    for unit in state.units:
        if unit == previous_unit:
            continue

        if unit.team != state.current_team:
            continue

        if unit_can_act(unit, state.current_phase):
            state.selected_unit = unit
            break


def handle_board_click(grid_x, grid_y):
    # клик по полю выбор своего отряда, движение, стрельба, натиск и ближний бой.
    if state.winner:
        return

    clicked_unit = get_unit_at(state.units, grid_x, grid_y)

    if clicked_unit and clicked_unit.team == state.current_team:
        if unit_can_act(clicked_unit, state.current_phase):
            state.selected_unit = clicked_unit
        elif clicked_unit.broken:
            log_event("О!")
        elif clicked_unit.ap < current_action_cost(state.current_phase):
            log_event("Не хватает AP!")
        else:
            log_event("Отряд уже ходил в этой фазе")

        return

    if not state.selected_unit:
        return

    if state.selected_unit.ap < current_action_cost(state.current_phase):
        log_event("Не хватает AP!")
        state.selected_unit = None
        return

    if state.current_phase in state.selected_unit.acted_phases:
        log_event("Отряд уже ходил в этой фазе")
        state.selected_unit = None
        return

    dist = distance(
        state.selected_unit.x,
        state.selected_unit.y,
        grid_x,
        grid_y,
    )

    target = clicked_unit

    if state.current_phase == "MOVEMENT":
        # проверка движения что бы обходило препятсвия, и не проходит на занятые поля
        if not can_move_to(state.selected_unit, grid_x, grid_y, state.units):
            log_event("Слишком далеко!")
            return

        old_x, old_y = state.selected_unit.x, state.selected_unit.y
        state.selected_unit.x = grid_x
        state.selected_unit.y = grid_y
        state.selected_unit.start_move_animation(old_x, old_y, grid_x, grid_y)
        log_event(f"{unit_name(state.selected_unit)} Идет на {grid_x},{grid_y}")
        state.selected_unit.ap -= 1

        if state.selected_unit.ap < 0:
            state.selected_unit.ap = 0

        state.mark_phase_action(state.selected_unit)
        select_next_ready_unit(state.selected_unit)
        return

    if not target or target.team == state.current_team:
        return
# чтобы стелять дальность, линия видимости и небыло ближнего боя
    if state.current_phase == "SHOOTING":
        if not can_shoot_target(state.selected_unit, target, state.units):
            if is_engaged(state.selected_unit, state.units):
                log_event("Отряд в ближнем бою!")
            elif dist > state.selected_unit.weapon.weapon_range:
                log_event("Цель далеко!")
            return

        before_hp = target.hp
        add_shot_effect(state, state.selected_unit, target)
        log_event(f"{unit_name(state.selected_unit)} Стреляет в {unit_name(target)}")
        attack(
            state.selected_unit,
            target,
            waaagh=state.waaagh_active,
        )
        add_damage_text(state, target, log_damage_result(target, before_hp))
        state.selected_unit.ap -= 1

        if state.selected_unit.ap < 0:
            state.selected_unit.ap = 0

        state.mark_phase_action(state.selected_unit)
        state.remove_dead_units()
        state.check_victory()
        select_next_ready_unit(state.selected_unit)
        return

    if state.current_phase == "CHARGE":
        
        # ставит атакующего на соседний с целью поле.
        if not can_charge_target(state.selected_unit, target, charge_max_range):
            log_event("Цель вне дальности натиска!")
            return

        from combat import attempt_charge

        old_x, old_y = state.selected_unit.x, state.selected_unit.y

        log_event(f"{unit_name(state.selected_unit)} Идет в натиск на {unit_name(target)}")

        if attempt_charge(state.selected_unit, target):
            state.selected_unit.start_move_animation(
                old_x,
                old_y,
                state.selected_unit.x,
                state.selected_unit.y,
                frames=18,
            )
            state.selected_unit.ap -= 2

            if state.selected_unit.ap < 0:
                state.selected_unit.ap = 0

            state.mark_phase_action(state.selected_unit)
            select_next_ready_unit(state.selected_unit)
        return

    if state.current_phase == "FIGHT":
        # Ближний бой разрешен только по соседним поле.
        if not can_fight_target(state.selected_unit, target):
            log_event("Цель слишком далеко")
            return

        before_hp = target.hp
        add_melee_effect(state, target)
        log_event(f"{unit_name(state.selected_unit)} Дерется с {unit_name(target)}")
        melee_attack(state.selected_unit, target)
        add_damage_text(state, target, log_damage_result(target, before_hp))
        state.selected_unit.ap -= 1

        if state.selected_unit.ap < 0:
            state.selected_unit.ap = 0

        state.mark_phase_action(state.selected_unit)
        state.remove_dead_units()
        state.check_victory()
        select_next_ready_unit(state.selected_unit)


def draw_game():
    # Кадр собирается слоями: поле, подсветки, юниты, эффекты, сайдбар
    screen.fill(black)
    draw_grid(screen)

    mx, my = pygame.mouse.get_pos()
    hovered_hex = pixel_to_hex(mx, my)

    if hovered_hex:
        hover_x, hover_y = hovered_hex
    else:
        hover_x = -1
        hover_y = -1

    state.hovered_target = get_unit_at(state.units, hover_x, hover_y)
    state.action_hint = "SELECT UNIT"

    if state.selected_unit and mx < game_width:
        # Подсказка в панели ACTION считается от текущего наведения мыши.
        state.action_hint = action_hint(
            state.selected_unit,
            state.hovered_target,
            hover_x,
            hover_y,
            state.current_phase,
            state.units,
            charge_max_range,
        )

    if state.selected_unit and unit_can_act(state.selected_unit, state.current_phase):
        
        if state.current_phase == "MOVEMENT":
            draw_movement_range(screen, state.selected_unit, state.units)
        elif state.current_phase == "SHOOTING":
            if not is_engaged(state.selected_unit, state.units):
                valid_targets = []

                for unit in state.units:
                    if can_shoot_target(state.selected_unit, unit, state.units):
                        valid_targets.append(unit)

                draw_invalid_targets(screen, state.selected_unit, state.units, valid_targets)
                draw_attack_range(screen, state.selected_unit, state.units)
        elif state.current_phase == "CHARGE":
            valid_targets = []

            for unit in state.units:
                if can_charge_target(state.selected_unit, unit, charge_max_range):
                    valid_targets.append(unit)

            draw_invalid_targets(screen, state.selected_unit, state.units, valid_targets)
            draw_target_range(
                screen,
                state.selected_unit,
                state.units,
                charge_max_range,
                (255, 140, 40, 120),
            )
        elif state.current_phase == "FIGHT":
            valid_targets = []

            for unit in state.units:
                if can_fight_target(state.selected_unit, unit):
                    valid_targets.append(unit)

            draw_invalid_targets(screen, state.selected_unit, state.units, valid_targets)
            draw_target_range(
                screen,
                state.selected_unit,
                state.units,
                1,
                (255, 60, 60, 140),
            )

    for unit in state.units:
        action_status = None

        if unit.team == state.current_team:
            action_status = unit_action_status(
                unit,
                state.current_team,
                state.current_phase,
            )

        unit.draw(
            screen,
            font,
            selected=unit == state.selected_unit,
            hovered=unit == state.hovered_target,
            engaged=is_engaged(unit, state.units),
            action_status=action_status,
            status_font=small_font,
        )

    draw_objective_indicators(screen, small_font, state.units)
    draw_effects(screen, font, state)
    update_effects(state)
    draw_floating_texts(screen, font, state)
    update_floating_texts(state)

    left_y, right_y = draw_sidebar(screen, small_font, state, mouse_pos=(mx, my))
    left_y = draw_target_preview(screen, small_font, state, left_y)
    right_y = draw_combat_log(screen, small_font, right_y)
    draw_dice_log(screen, small_font, right_y)
    draw_turn_header(screen, font, state)
    draw_full_log_overlay(screen, font, small_font, state)
    draw_victory_screen(screen, font, small_font, state)

    if pause_menu_visible:
        draw_pause_menu(
            screen,
            font,
            small_font,
            state,
            app_settings["dice_delay_ms"],
        )

    draw_help_overlay(screen, font, small_font, state)


running = True

while running:

    if start_screen_visible:
        draw_start_screen(
            screen,
            font,
            small_font,
            state.ai_orks_enabled,
            app_settings["dice_delay_ms"],
        )
    else:
        draw_game()

        if (
            state.ai_orks_enabled
            and state.current_team == 2
            and not state.full_log_visible
            and not state.help_visible
            and not pause_menu_visible
        ):
            # бот делает не весь ход сразу, для удобства
            now = pygame.time.get_ticks()

            if now >= state.ai_timer:
                ai_take_turn_step(state)
                state.ai_timer = now + ai_turn_delay_ms

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Стартовый экран 
            if start_screen_visible:
                if event.key == pygame.K_1:
                    state.ai_orks_enabled = False
                    persist_ai_setting()
                elif event.key == pygame.K_2:
                    state.ai_orks_enabled = True
                    persist_ai_setting()
                elif event.key == pygame.K_LEFTBRACKET:
                    adjust_dice_delay(-20)
                elif event.key == pygame.K_RIGHTBRACKET:
                    adjust_dice_delay(20)
                elif event.key == pygame.K_RETURN:
                    state.reset(ai_orks_enabled=state.ai_orks_enabled)
                    start_screen_visible = False
                continue

            if event.key == pygame.K_ESCAPE:
                # ESC сперва закрывает справку, а уже потом открывает/закрыва паузу
                if state.help_visible:
                    state.help_visible = False
                    continue
                if state.winner:
                    continue
                pause_menu_visible = not pause_menu_visible
                continue

            if state.winner:
                if event.key == pygame.K_r:
                    reset_game()
                    start_screen_visible = True
                elif event.key == pygame.K_m:
                    start_screen_visible = True
                    state.full_log_visible = False
                continue

            if pause_menu_visible:
                if event.key == pygame.K_r:
                    reset_game()
                    pause_menu_visible = False
                elif event.key == pygame.K_h:
                    state.help_visible = not state.help_visible
                elif event.key == pygame.K_m:
                    start_screen_visible = True
                    pause_menu_visible = False
                    state.full_log_visible = False
                elif event.key == pygame.K_i:
                    toggle_ai()
                elif event.key == pygame.K_LEFTBRACKET:
                    adjust_dice_delay(-20)
                elif event.key == pygame.K_RIGHTBRACKET:
                    adjust_dice_delay(20)
                continue

            if event.key == pygame.K_r:
                reset_game()
                start_screen_visible = True
            elif event.key == pygame.K_RETURN:
                ready_count = 0

                for unit in state.units:
                    if unit.team == state.current_team:
                        if unit_can_act(unit, state.current_phase):
                            ready_count += 1

                if ready_count > 0:
                    log_event(f"Готовых отрядов: {ready_count}")

                state.advance_phase()
            elif event.key == pygame.K_SPACE:
                state.activate_waaagh()
            elif event.key == pygame.K_l:
                state.full_log_visible = not state.full_log_visible
            elif event.key == pygame.K_h:
                state.help_visible = not state.help_visible
            elif event.key == pygame.K_i:
                toggle_ai()
            elif event.key == pygame.K_LEFTBRACKET:
                adjust_dice_delay(-20)
            elif event.key == pygame.K_RIGHTBRACKET:
                adjust_dice_delay(20)

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and not start_screen_visible
            and not pause_menu_visible
            and not state.help_visible
        ):
            if state.winner:
                continue

            if state.ai_orks_enabled and state.current_team == 2:
                continue

            if next_phase_rect.collidepoint(event.pos):
                state.advance_phase()
                continue

            if waaagh_rect.collidepoint(event.pos):
                state.activate_waaagh()
                continue

            if event.pos[0] >= game_width:
                roster_unit = get_sidebar_roster_unit_at(event.pos, state)

                if (
                    roster_unit
                    and roster_unit.team == state.current_team
                    and unit_can_act(roster_unit, state.current_phase)
                ):
                    state.selected_unit = roster_unit

                continue

            clicked_hex = pixel_to_hex(*event.pos)

            if not clicked_hex:
                continue

            handle_board_click(*clicked_hex)

    clock.tick(60)

pygame.quit()
sys.exit()
