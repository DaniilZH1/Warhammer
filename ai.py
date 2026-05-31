from board import cover_tiles, is_in_cover, objective_tiles
from combat import (
    attack,
    attempt_charge,
    effective_weapon_attacks,
    log_event,
    melee_attack,
    wound_roll_needed,
)
from effects import add_damage_text, add_melee_effect, add_shot_effect
from game_state import ai_charge_comfort_range, charge_max_range
from localization import phase_label, role_label
from rules import (
    can_charge_target,
    can_fight_target,
    can_move_to,
    can_shoot_target,
    controlled_objective_count,
    count_objective_control,
    distance,
    has_line_of_sight_between,
    objective_statuses,
    reachable_tiles,
    unit_can_act,
)
from settings import grid_size


def ai_units_ready(state, team=None):
    # Находим отряды, которыми бот сейчас может походить.
    if team is None:
        team = state.current_team

    result = []

    for unit in state.units:
        if unit.team == team:
            if unit_can_act(unit, state.current_phase):
                result.append(unit)

    return result


def ai_enemy_targets(state, unit):
    result = []

    for target in state.units:
        if target.team != unit.team:
            result.append(target)

    return result


def ai_nearest_target(state, unit):
    enemies = ai_enemy_targets(state, unit)

    if not enemies:
        return None

    best_enemy = None
    best_distance = None

    for enemy in enemies:
        enemy_distance = distance(unit.x, unit.y, enemy.x, enemy.y)

        if best_enemy is None or enemy_distance < best_distance:
            best_enemy = enemy
            best_distance = enemy_distance

    return best_enemy


def roll_success_chance(needed):
    if needed < 2:
        needed = 2

    if needed > 6:
        needed = 6

    return (7 - needed) / 6


def ai_modified_save(attacker, target):
    modified_save = target.armor_save - attacker.weapon.ap

    if is_in_cover(target):
        modified_save -= 1

    if modified_save < 2:
        modified_save = 2

    if modified_save > 6:
        modified_save = 6

    return modified_save


def ai_expected_shoot_damage(state, unit, target):
    # Примерно считаем, сколько урона может нанести выстрел.
    
    dist = distance(unit.x, unit.y, target.x, target.y)
    attacks = effective_weapon_attacks(unit)

    if (
        "rapid_fire" in unit.weapon.special_rules
        and dist <= unit.weapon.weapon_range // 2
    ):
        attacks += effective_weapon_attacks(unit)

    if state.waaagh_active:
        attacks += 1

    hit = roll_success_chance(unit.ballistic_skill)
    wound = roll_success_chance(
        wound_roll_needed(unit.weapon.strength, target.toughness)
    )
    failed_save = 1 - roll_success_chance(ai_modified_save(unit, target))
    base_damage = attacks * hit * wound * failed_save * unit.weapon.damage

    if "sustained_hits" in unit.weapon.special_rules:
        base_damage += attacks * (1 / 6) * wound * failed_save * unit.weapon.damage

    return base_damage


def ai_movement_targets(state, unit):
    
    own_control = count_objective_control(state.units, unit.team)
    enemy_control = 0
    checked_teams = []

    for target in ai_enemy_targets(state, unit):
        if target.team not in checked_teams:
            checked_teams.append(target.team)
            enemy_control += count_objective_control(state.units, target.team)

    if own_control <= enemy_control:
        return objective_tiles

    enemy_tiles = []

    for target in ai_enemy_targets(state, unit):
        enemy_tiles.append((target.x, target.y))

    if enemy_tiles:
        return enemy_tiles

    return objective_tiles


def ai_tile_has_shot(unit, x, y, target):
    return (
        distance(x, y, target.x, target.y) <= unit.weapon.weapon_range
        and has_line_of_sight_between(x, y, target.x, target.y)
    )


def ai_best_visible_target_from_tile(state, unit, x, y):
    best_target = None
    best_priority = None

    for target in ai_enemy_targets(state, unit):
        if ai_tile_has_shot(unit, x, y, target):
            priority = ai_target_priority(state, unit, target)

            if best_target is None or priority > best_priority:
                best_target = target
                best_priority = priority

    return best_target


def ai_target_priority(state, unit, target):
    # Чем больше число, тем сильнее бот хочет атаковать эту цель.
    expected_damage = ai_expected_shoot_damage(state, unit, target)
    priority = expected_damage * 10

    damage_limit = expected_damage

    if damage_limit < 1:
        damage_limit = 1

    if target.hp <= damage_limit:
        priority += 8

    if (target.x, target.y) in objective_tiles:
        priority += 5

    for status in objective_statuses(state.units):
        if status["controller"] == target.team:
            priority += 2

    if target.role in ("plasma", "heavy", "nob", "rokkit"):
        priority += 3

    enemy_control = controlled_objective_count(state.units, target.team)
    own_control = controlled_objective_count(state.units, unit.team)
    if enemy_control >= own_control:
        priority += 2

    close_bonus = 4 - distance(unit.x, unit.y, target.x, target.y)

    if close_bonus < 0:
        close_bonus = 0

    priority += close_bonus * 0.5

    models = target.models

    if models < 0:
        models = 0

    priority += models * 0.05

    return priority


def ai_best_shoot_target(state, unit):
    best_target = None
    best_priority = None

    for target in ai_enemy_targets(state, unit):
        if can_shoot_target(unit, target, state.units):
            priority = ai_target_priority(state, unit, target)

            if best_target is None or priority > best_priority:
                best_target = target
                best_priority = priority

    return best_target


def ai_best_charge_target(state, unit, max_charge_range):
    best_target = None
    best_priority = None
    best_distance = None

    for target in ai_enemy_targets(state, unit):
        target_distance = distance(unit.x, unit.y, target.x, target.y)

        if can_charge_target(unit, target, charge_max_range):
            if target_distance <= max_charge_range:
                priority = ai_target_priority(state, unit, target)

                if best_target is None:
                    best_target = target
                    best_priority = priority
                    best_distance = target_distance
                elif priority > best_priority:
                    best_target = target
                    best_priority = priority
                    best_distance = target_distance
                elif priority == best_priority and target_distance < best_distance:
                    best_target = target
                    best_priority = priority
                    best_distance = target_distance

    return best_target


def ai_should_use_waaagh(state):
    # Бот включает WAAAGH только если рядом есть враг.
    if state.waaagh_used or state.waaagh_active or state.current_team != 2:
        return False

    if state.current_phase not in ("SHOOTING", "CHARGE", "FIGHT"):
        return False

    for unit in state.units:
        if unit.team != 2:
            continue

        target = ai_nearest_target(state, unit)

        if not target:
            continue

        dist = distance(unit.x, unit.y, target.x, target.y)

        if dist <= 1 or dist <= ai_charge_comfort_range:
            return True

        half_range = unit.weapon.weapon_range // 2

        if half_range < 1:
            half_range = 1

        if dist <= half_range:
            return True

    return False


def ai_move_unit(state, unit):
    # Бот выбирает клетку, которая выглядит полезнее всего.
    targets = ai_movement_targets(state, unit)
    best_tile = None
    best_score = None

    for x, y in reachable_tiles(unit, state.units):
        goal_distance = None

        for target_x, target_y in targets:
            dist_to_goal = distance(x, y, target_x, target_y)

            if goal_distance is None or dist_to_goal < goal_distance:
                goal_distance = dist_to_goal

        nearest_enemy = ai_nearest_target(state, unit)
        enemy_distance = 0

        if nearest_enemy:
            enemy_distance = distance(x, y, nearest_enemy.x, nearest_enemy.y)

        visible_target = ai_best_visible_target_from_tile(state, unit, x, y)
        visible_priority = 0

        if visible_target:
            visible_priority = ai_target_priority(state, unit, visible_target)

        if visible_target:
            has_visible_target_score = 0
        else:
            has_visible_target_score = 1

        if (x, y) in objective_tiles:
            objective_score = 0
        else:
            objective_score = 1

        if (x, y) in cover_tiles:
            cover_score = 0
        else:
            cover_score = 1

        score = (
            has_visible_target_score,
            -visible_priority,
            goal_distance,
            enemy_distance,
            objective_score,
            cover_score,
        )

        if best_score is None or score < best_score:
            best_score = score
            best_tile = (x, y)

    if not best_tile:
        return False

    old_x, old_y = unit.x, unit.y
    unit.x, unit.y = best_tile
    unit.start_move_animation(old_x, old_y, unit.x, unit.y)
    unit.ap -= 1

    if unit.ap < 0:
        unit.ap = 0

    state.mark_phase_action(unit)
    from combat import log_event

    log_event(f"AI: {role_label(unit.role)} идет на {best_tile[0]},{best_tile[1]}")
    return True


def ai_shoot_unit(state, unit):
    # Бот стреляет той же функцией, что и игрок.
    target = ai_best_shoot_target(state, unit)

    if not target:
        return False

    before_hp = target.hp
    add_shot_effect(state, unit, target)
    log_event(f"{role_label(unit.role)} стреляет в {role_label(target.role)}")
    attack(unit, target, waaagh=state.waaagh_active)
    damage = before_hp - target.hp

    if damage < 0:
        damage = 0

    if damage:
        log_event(f"{role_label(target.role)} получает {damage} урн")
    else:
        log_event("Без урона")

    add_damage_text(state, target, damage)
    unit.ap -= 1

    if unit.ap < 0:
        unit.ap = 0

    state.mark_phase_action(unit)
    state.remove_dead_units()
    state.check_victory()
    return True


def ai_charge_unit(state, unit):
    # Без WAAAGH бот не любит слишком дальний натиск.
    if state.waaagh_active:
        max_charge_range = charge_max_range
    else:
        max_charge_range = ai_charge_comfort_range

    target = ai_best_charge_target(state, unit, max_charge_range)

    if not target:
        return False

    old_x, old_y = unit.x, unit.y

    log_event(f"{role_label(unit.role)} идет в натиск на {role_label(target.role)}")

    if not attempt_charge(unit, target):
        state.mark_phase_action(unit)
        return True

    unit.start_move_animation(old_x, old_y, unit.x, unit.y, frames=18)
    unit.ap -= 2

    if unit.ap < 0:
        unit.ap = 0

    state.mark_phase_action(unit)
    return True


def ai_fight_unit(state, unit):
    # В ближнем бою бот выбирает лучшую соседнюю цель.
    target = None
    best_priority = None
    best_hp = None

    for enemy in ai_enemy_targets(state, unit):
        if can_fight_target(unit, enemy):
            priority = ai_target_priority(state, unit, enemy)

            if target is None:
                target = enemy
                best_priority = priority
                best_hp = enemy.hp
            elif priority > best_priority:
                target = enemy
                best_priority = priority
                best_hp = enemy.hp
            elif priority == best_priority and enemy.hp < best_hp:
                target = enemy
                best_priority = priority
                best_hp = enemy.hp

    if not target:
        return False

    before_hp = target.hp
    add_melee_effect(state, target)
    log_event(f"{role_label(unit.role)} дерется с {role_label(target.role)}")
    melee_attack(unit, target)
    damage = before_hp - target.hp

    if damage < 0:
        damage = 0

    if damage:
        log_event(f"{role_label(target.role)} получает {damage} урн")
    else:
        log_event("Без урона")

    add_damage_text(state, target, damage)
    unit.ap -= 1

    if unit.ap < 0:
        unit.ap = 0

    state.mark_phase_action(unit)
    state.remove_dead_units()
    state.check_victory()
    return True


def ai_take_team_step(state):
    # За один раз бот делает только одно действие, чтобы ход было видно.
    if state.winner:
        return

    state.selected_unit = None

    if ai_should_use_waaagh(state):
        state.activate_waaagh()

    ready = ai_units_ready(state, state.current_team)

    if not ready:
        from combat import log_event

        log_event("Нет готовых отрядов")
        state.advance_phase()
        return

    for unit in ready:
        if state.current_phase == "MOVEMENT" and ai_move_unit(state, unit):
            return

        if state.current_phase == "SHOOTING" and ai_shoot_unit(state, unit):
            return

        if state.current_phase == "CHARGE" and ai_charge_unit(state, unit):
            return

        if state.current_phase == "FIGHT" and ai_fight_unit(state, unit):
            return

    from combat import log_event

    log_event(f"Нет действий в фазе {phase_label(state.current_phase)}")
    state.advance_phase()


def ai_take_turn_step(state):
    if state.winner or state.current_team != 2:
        return

    ai_take_team_step(state)
