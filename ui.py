import pygame

from ai import ai_expected_shoot_damage
from combat import (
    combat_log,
    dice_log,
    dice_to_symbol,
    effective_melee_attacks,
    effective_weapon_attacks,
    hit_chance,
    save_chance,
    wound_chance,
)
from game_state import victory_points
from localization import (
    dice_label,
    faction_label,
    hint_label,
    objective_label,
    phase_label,
    role_label,
    role_short_label,
    status_label,
    team_label,
    weapon_label,
)
from rules import (
    has_line_of_sight,
    objective_statuses,
    ready_units,
    unit_action_status,
)
from settings import *

# Тут рисуется интерфейс игры.
next_phase_rect = pygame.Rect(game_width + 20, 92, ui_width - 40, 32)
waaagh_rect = pygame.Rect(game_width + 20, 130, ui_width - 40, 32)
sidebar_x = game_width + 20
sidebar_padding = 12
sidebar_left_x = game_width + sidebar_padding
sidebar_col_gap = 12
sidebar_col_width = (ui_width - sidebar_padding * 2 - sidebar_col_gap) // 2
sidebar_right_x = sidebar_left_x + sidebar_col_width + sidebar_col_gap
sidebar_line_height = 22
sidebar_section_gap = 18
sidebar_rule_color = (100, 100, 100)
roster_row_height = 24
control_start_y = 166


def draw_centered_text(screen, font, text, y, color=white):
    rendered = font.render(text, True, color)
    screen.blit(
        rendered,
        (window_width // 2 - rendered.get_width() // 2, y),
    )


def draw_ui_line(screen, small_font, text, x, y, color=white, max_chars=30):
    # Если текст слишком длинный, обрезаем его.
    text = str(text)

    if len(text) > max_chars:
        text = text[:max_chars - 3] + "..."

    screen.blit(
        small_font.render(text, True, color),
        (x, y),
    )


def draw_button(screen, small_font, rect, label, enabled=True):
    if enabled:
        fill = (70, 70, 70)
        outline = (160, 160, 160)
        text_color = white
    else:
        fill = (45, 45, 45)
        outline = (90, 90, 90)
        text_color = (140, 140, 140)

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


def draw_mode_card(screen, font, small_font, rect, title, body, selected):
    if selected:
        fill = (52, 58, 60)
        outline = (255, 220, 100)
        title_color = (255, 220, 100)
    else:
        fill = (34, 36, 38)
        outline = (105, 110, 112)
        title_color = white

    pygame.draw.rect(screen, fill, rect, border_radius=6)
    pygame.draw.rect(screen, outline, rect, 2, border_radius=6)

    title_text = font.render(title, True, title_color)
    screen.blit(
        title_text,
        (rect.centerx - title_text.get_width() // 2, rect.y + 24),
    )

    body_text = small_font.render(body, True, (210, 210, 210))
    screen.blit(
        body_text,
        (rect.centerx - body_text.get_width() // 2, rect.y + 68),
    )


def draw_sidebar_rule(screen, y, x=sidebar_left_x, width=sidebar_col_width):
    pygame.draw.line(
        screen,
        sidebar_rule_color,
        (x, y),
        (x + width, y),
        2,
    )

    return y + sidebar_section_gap


def draw_sidebar_lines(
    screen,
    small_font,
    lines,
    y,
    color=white,
    line_height=sidebar_line_height,
    x=sidebar_left_x,
    max_chars=30,
):
    for line in lines:
        draw_ui_line(screen, small_font, line, x, y, color, max_chars=max_chars)
        y += line_height

    return y


def draw_controls(screen, small_font, state, y, x=sidebar_left_x):
    # Рисуем список горячих клавиш.
    y = draw_sidebar_rule(screen, y, x)

    if state.ai_orks_enabled:
        ai_text = "Вкл"
    else:
        ai_text = "Выкл"

    controls = []
    controls.append("Enter фаза")
    controls.append("R сброс")
    controls.append("L весь лог")
    controls.append("H помощь")
    controls.append(f"I AI орков: {ai_text}")
    controls.append("[/] кубы")
    controls.append("Space WAAAGH")

    return draw_sidebar_lines(
        screen,
        small_font,
        controls,
        y,
        (170, 190, 210),
        18,
        x=x,
        max_chars=18,
    ) + sidebar_section_gap


def roster_row_rect(index, y, x=sidebar_right_x):
    return pygame.Rect(
        x,
        y + index * roster_row_height,
        sidebar_col_width,
        roster_row_height - 3,
    )


def draw_unit_roster(screen, small_font, state, y, mouse_pos=None, x=sidebar_right_x):
    # Рисуем список отрядов справа.
    y = draw_sidebar_rule(screen, y, x)
    draw_ui_line(screen, small_font, "Отряды", x, y, white)
    y += 24

    index = 0

    for unit in state.units:
        if index >= 8:
            break

        rect = roster_row_rect(index, y, x)
        selected = unit == state.selected_unit
        hovered = mouse_pos and rect.collidepoint(mouse_pos)
        active = unit.team == state.current_team
        fill = (46, 46, 46)

        if selected:
            fill = (62, 72, 78)

        if hovered:
            fill = (58, 64, 68)

        outline = (80, 80, 80)

        if selected:
            outline = (255, 220, 100)

        if hovered and active:
            outline = (170, 190, 210)

        text_color = (155, 155, 155)

        if active:
            text_color = white
        status = status_label(unit_action_status(
            unit,
            state.current_team,
            state.current_phase,
        )[0])
        name = role_short_label(unit.role)
        line = f"{name} HP:{unit.hp} AP:{unit.ap} {status}"

        pygame.draw.rect(screen, fill, rect, border_radius=3)
        pygame.draw.rect(screen, outline, rect, 1, border_radius=3)
        draw_ui_line(
            screen,
            small_font,
            line,
            rect.x + 5,
            rect.y + 3,
            text_color,
            max_chars=16,
        )

        index += 1

    return y + len(state.units[:8]) * roster_row_height + sidebar_section_gap


def draw_objectives_panel(screen, small_font, state, y, x=sidebar_left_x):
    # Рисуем контроль точек.
    y = draw_sidebar_rule(screen, y, x)
    draw_ui_line(screen, small_font, "Точки", x, y, white)
    y += 24

    for status in objective_statuses(state.units):
        if status["controller"] == 1:
            control = "M"
            color = (100, 180, 255)
        elif status["controller"] == 2:
            control = "O"
            color = (100, 255, 100)
        else:
            control = "-"
            color = (180, 180, 180)

        line = (
            f"{objective_label(status['name'])} "
            f"M:{status['marine']} O:{status['ork']} К:{control}"
        )
        draw_ui_line(screen, small_font, line, x, y, color, max_chars=18)
        y += 18

    return y + sidebar_section_gap


def draw_action_panel(screen, small_font, state, y, x=sidebar_left_x):
    # Рисуем подсказку, что будет при клике.
    y = draw_sidebar_rule(screen, y, x)
    draw_ui_line(screen, small_font, "Действие", x, y, white)
    y += 24

    hint = getattr(state, "action_hint", "SELECT UNIT")
    visible_hint = hint_label(hint)
    hint_color = (255, 220, 100)

    if hint in (
        "BLOCKED",
        "BROKEN",
        "NO LOS",
        "OUT OF RANGE",
        "OUT OF MOVE",
        "OUT OF CHARGE",
    ):
        hint_color = (255, 120, 100)
    elif hint in ("MOVE", "SHOOT", "CHARGE", "FIGHT"):
        hint_color = (100, 255, 140)

    draw_ui_line(screen, small_font, visible_hint, x, y, hint_color, max_chars=18)
    y += 22

    ready_count = len(ready_units(state.units, state.current_team, state.current_phase))
    if ready_count > 0:
        draw_ui_line(
            screen,
            small_font,
            f"Готовы: {ready_count}",
            x,
            y,
            (170, 190, 210),
            max_chars=18,
        )
    else:
        draw_ui_line(
            screen,
            small_font,
            "Enter фаза",
            x,
            y,
            (170, 190, 210),
            max_chars=18,
        )

    return y + 22 + sidebar_section_gap


def get_roster_unit_at(pos, state, y, x=sidebar_right_x):
    index = 0

    for unit in state.units:
        if index >= 8:
            break

        if roster_row_rect(index, y, x).collidepoint(pos):
            return unit

        index += 1

    return None


def get_sidebar_roster_unit_at(pos, state):
    return get_roster_unit_at(pos, state, control_start_y + 24, sidebar_right_x)


def draw_sidebar(screen, small_font, state, mouse_pos=None):
    # Рисуем весь правый сайдбар.
    pygame.draw.rect(
        screen,
        (40, 40, 40),
        (game_width, 0, ui_width, window_height),
    )

    draw_ui_line(
        screen,
        small_font,
        f"Поб M:{state.marine_vp} O:{state.ork_vp}/{victory_points}",
        sidebar_left_x,
        15,
        (255, 220, 100),
    )

    draw_ui_line(
        screen,
        small_font,
        team_label(state.current_team),
        sidebar_left_x + 95,
        42,
        white,
    )

    draw_ui_line(
        screen,
        small_font,
        phase_label(state.current_phase),
        sidebar_left_x + 190,
        65,
        (255, 220, 100),
    )

    draw_button(screen, small_font, next_phase_rect, "След. фаза", enabled=state.winner is None)
    draw_button(
        screen,
        small_font,
        waaagh_rect,
        "WAAAGH",
        enabled=state.winner is None and state.current_team == 2 and not state.waaagh_used,
    )

    if state.winner:
        if state.winner == 1:
            winner_name = "Марины"
        else:
            winner_name = "Орки"

        stats = []
        stats.append(f"{winner_name} Победа")
        stats.append("")
        stats.append("R")
        stats.append("Новая игра")
    elif state.selected_unit:
        status = status_label(unit_action_status(
            state.selected_unit,
            state.current_team,
            state.current_phase,
        )[0])
        stats = [
            role_label(state.selected_unit.role),
            f"Модели: {state.selected_unit.models}/{state.selected_unit.max_models}",
            f"HP: {state.selected_unit.hp}",
            f"Стойк: {state.selected_unit.toughness}",
            f"Сейв: {state.selected_unit.armor_save}+",
            f"AP: {state.selected_unit.ap}/{state.selected_unit.max_ap}",
            f"Статус: {status}",
            "",
            weapon_label(state.selected_unit.weapon.name),
            f"Атк: {effective_weapon_attacks(state.selected_unit)}/{state.selected_unit.weapon.attacks}",
            f"Сила: {state.selected_unit.weapon.strength}",
            f"AP: {state.selected_unit.weapon.ap}",
            f"Урн: {state.selected_unit.weapon.damage}",
            f"Дальн: {state.selected_unit.weapon.weapon_range}",
            f"Бой: {effective_melee_attacks(state.selected_unit)}/{state.selected_unit.melee_attacks}",
        ]
    else:
        stats = [
            "Выбери отряд",
            "",
            "Enter",
            "След. фаза",
        ]

    left_y = draw_controls(screen, small_font, state, control_start_y, sidebar_left_x)
    left_y = draw_objectives_panel(screen, small_font, state, left_y, sidebar_left_x)
    left_y = draw_action_panel(screen, small_font, state, left_y, sidebar_left_x)
    left_y = draw_sidebar_lines(
        screen,
        small_font,
        stats,
        left_y,
        white,
        20,
        x=sidebar_left_x,
        max_chars=18,
    ) + sidebar_section_gap

    right_y = draw_unit_roster(
        screen,
        small_font,
        state,
        control_start_y,
        mouse_pos=mouse_pos,
        x=sidebar_right_x,
    )

    if left_y > right_y:
        final_y = left_y
    else:
        final_y = right_y

    return final_y, right_y


def draw_target_preview(screen, small_font, state, y, x=sidebar_left_x):
    # Рисуем информацию о цели под мышкой.
    if (
        not state.selected_unit
        or not state.hovered_target
        or state.hovered_target.team == state.selected_unit.team
    ):
        return y

    hit = hit_chance(state.selected_unit.ballistic_skill)
    wound = wound_chance(
        state.selected_unit.weapon.strength,
        state.hovered_target.toughness,
    )
    save = save_chance(state.hovered_target.armor_save)
    expected_damage = ai_expected_shoot_damage(
        state,
        state.selected_unit,
        state.hovered_target,
    )
    los_text = "Обзор: да"

    if not has_line_of_sight(state.selected_unit, state.hovered_target):
        los_text = "Обзор: нет"

    y = draw_sidebar_rule(screen, y, x)

    preview = [
        "Цель",
        faction_label(state.hovered_target.faction).upper(),
        f"Поп: {hit}%",
        f"Ран: {wound}%",
        f"Сейв: {save}%",
        f"ОЖ урн: {expected_damage:.1f}",
        los_text,
        f"Урн: {state.selected_unit.weapon.damage}",
    ]

    return draw_sidebar_lines(
        screen,
        small_font,
        preview,
        y,
        (255, 220, 100),
        x=x,
        max_chars=18,
    ) + sidebar_section_gap


def draw_combat_log(screen, small_font, y, x=sidebar_right_x):
    # Рисуем короткий лог боя.
    y = draw_sidebar_rule(screen, y, x)

    draw_ui_line(screen, small_font, "Лог", x, y, white)
    y += 25

    dice_block_height = 25 + sidebar_line_height * 2 + sidebar_section_gap
    available_height = window_height - y - dice_block_height
    max_lines = available_height // sidebar_line_height

    if max_lines < 1:
        max_lines = 1

    if max_lines > 10:
        max_lines = 10

    return draw_sidebar_lines(
        screen,
        small_font,
        combat_log[-max_lines:],
        y,
        (210, 210, 210),
        x=x,
        max_chars=18,
    ) + sidebar_section_gap


def draw_dice_log(screen, small_font, y, x=sidebar_right_x):
    y = draw_sidebar_rule(screen, y, x)

    draw_ui_line(screen, small_font, "Кубы", x, y, white)
    y += 25

    for roll_type, value in dice_log[-2:]:
        draw_ui_line(
            screen,
            small_font,
            f"{dice_label(roll_type)}: {dice_to_symbol(value)}",
            x,
            y,
            white,
            max_chars=18,
        )
        y += sidebar_line_height

    return y


def draw_full_log_overlay(screen, font, small_font, state):
    # Рисуем большой лог поверх поля.
    if not state.full_log_visible:
        return

    overlay = pygame.Surface((game_width - 120, window_height - 120), pygame.SRCALPHA)
    overlay.fill((20, 20, 20, 235))

    rect = overlay.get_rect(topleft=(60, 60))
    screen.blit(overlay, rect.topleft)
    pygame.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=4)

    screen.blit(
        font.render("Боевой лог", True, white),
        (rect.x + 20, rect.y + 16),
    )

    y = rect.y + 55
    max_lines = (rect.height - 80) // sidebar_line_height

    for line in combat_log[-max_lines:]:
        screen.blit(
            small_font.render(str(line), True, (220, 220, 220)),
            (rect.x + 20, y),
        )
        y += sidebar_line_height


def draw_help_overlay(screen, font, small_font, state):
    # Рисуем окно помощи.
    if not state.help_visible:
        return

    overlay = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    screen.blit(overlay, (0, 0))

    rect = pygame.Rect(window_width // 2 - 260, window_height // 2 - 245, 520, 490)
    pygame.draw.rect(screen, (28, 30, 32), rect, border_radius=6)
    pygame.draw.rect(screen, (255, 220, 100), rect, 2, border_radius=6)

    title = font.render("Как играть", True, (255, 220, 100))
    screen.blit(title, (rect.centerx - title.get_width() // 2, rect.y + 24))

    lines = [
        "ЛКМ по своему: выбор",
        "ЛКМ по гексу: движение",
        "ЛКМ по врагу: атака / натиск / бой",
        "Enter: следующая фаза",
        "L: полный боевой лог",
        "I: Вкл / Выкл AI орков",
        "Space: WAAAGH в ход орков",
        "[ / ]: скорость кубов",
        "R: новая игра",
        "Esc: пауза / закрыть",
        "",
        f"Победа: {victory_points} Поб или разгром",
        "Точки дают Поб в начале хода",
        "H: закрыть справку",
    ]

    y = rect.y + 82
    for line in lines:
        if ":" in line:
            color = (170, 190, 210)
        else:
            color = white

        text = small_font.render(line, True, color)
        screen.blit(text, (rect.x + 54, y))
        y += 28


def draw_pause_menu(screen, font, small_font, state, dice_delay_ms=80):
    overlay = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    rect = pygame.Rect(window_width // 2 - 180, window_height // 2 - 150, 360, 300)
    pygame.draw.rect(screen, (28, 30, 32), rect, border_radius=6)
    pygame.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=6)

    title = font.render("Пауза", True, (255, 220, 100))
    screen.blit(
        title,
        (rect.centerx - title.get_width() // 2, rect.y + 26),
    )

    if state.ai_orks_enabled:
        ai_state = "Вкл"
    else:
        ai_state = "Выкл"

    lines = []
    lines.append("Esc продолжить")
    lines.append("R новая игра")
    lines.append("H помощь")
    lines.append("M выбор режима")
    lines.append(f"I AI орков: {ai_state}")
    lines.append(f"[/] кубы: {dice_delay_ms}мс")

    y = rect.y + 92
    for line in lines:
        text = small_font.render(line, True, white)
        screen.blit(
            text,
            (rect.centerx - text.get_width() // 2, y),
        )
        y += 32


def draw_victory_screen(screen, font, small_font, state):
    if not state.winner:
        return

    overlay = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    screen.blit(overlay, (0, 0))

    rect = pygame.Rect(window_width // 2 - 220, window_height // 2 - 170, 440, 340)
    pygame.draw.rect(screen, (28, 30, 32), rect, border_radius=6)
    pygame.draw.rect(screen, (255, 220, 100), rect, 2, border_radius=6)

    if state.winner == 1:
        winner_name = "Космодесант"
    else:
        winner_name = "Орки"

    if state.victory_reason == "vp":
        reason = "Победа по очкам"
    else:
        reason = "Победа разгромом"

    title = font.render(f"{winner_name}: Победа", True, (255, 220, 100))
    screen.blit(
        title,
        (rect.centerx - title.get_width() // 2, rect.y + 28),
    )

    lines = []
    lines.append(reason)
    lines.append(f"Поб M:{state.marine_vp} O:{state.ork_vp}")
    lines.append(f"Ход {state.turn_number}")
    lines.append("")
    lines.append("R новая игра")
    lines.append("M выбор режима")

    y = rect.y + 88
    for line in lines:
        text = small_font.render(line, True, white)
        screen.blit(
            text,
            (rect.centerx - text.get_width() // 2, y),
        )
        y += 34


def draw_turn_header(screen, font, state):
    if state.winner:
        if state.winner == 1:
            winner_name = "Космодесант"
        else:
            winner_name = "Орки"

        screen.blit(
            font.render(f"{winner_name}: Победа!", True, (255, 220, 100)),
            (20, 20),
        )
        screen.blit(
            font.render("R - новая игра", True, white),
            (20, 60),
        )
        return

    if state.current_team == 1:
        turn_text = "Ход Космодесанта"
        turn_color = (100, 180, 255)
    else:
        turn_text = "Ход орков"
        turn_color = (100, 255, 100)

    screen.blit(font.render(turn_text, True, turn_color), (20, 20))
    screen.blit(
        font.render(f"Фаза: {phase_label(state.current_phase)}", True, (255, 220, 100)),
        (20, 60),
    )

    if state.waaagh_active:
        screen.blit(
            font.render("WAAAGH активен", True, (100, 255, 100)),
            (20, 100),
        )


def draw_start_screen(screen, font, small_font, ai_orks_enabled, dice_delay_ms=80):
    # Рисуем стартовый экран.
    screen.fill(black)

    draw_centered_text(screen, font, "Мини Warhammer", 120, (255, 220, 100))
    draw_centered_text(
        screen,
        small_font,
        f"v{version} прототип",
        158,
        (210, 210, 210),
    )

    manual_rect = pygame.Rect(145, 230, 300, 140)
    ai_rect = pygame.Rect(555, 230, 300, 140)

    draw_mode_card(
        screen,
        font,
        small_font,
        manual_rect,
        "Космодесант vs орки",
        "Ручное управление за обе стороны",
        not ai_orks_enabled,
    )
    draw_mode_card(
        screen,
        font,
        small_font,
        ai_rect,
        "Космодесант vs AI",
        "Орки ходят сами",
        ai_orks_enabled,
    )

    if ai_orks_enabled:
        mode = "Космодесант vs AI орков"
    else:
        mode = "Космодесант vs орки"

    draw_centered_text(screen, small_font, f"Режим: {mode}", 430, (255, 220, 100))
    draw_centered_text(screen, small_font, f"Скорость кубов: {dice_delay_ms}мс", 462, white)
    draw_centered_text(screen, small_font, "1 / 2 выбор режима", 505, white)
    draw_centered_text(screen, small_font, "[ / ] скорость кубов", 535, white)
    draw_centered_text(screen, small_font, "H помощь в игре", 565, white)
    draw_centered_text(screen, small_font, "Enter старт", 595, white)
