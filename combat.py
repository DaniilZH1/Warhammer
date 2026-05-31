import random
import builtins
import pygame

from board import is_blocked, is_in_cover

# Тут бросаются кубики и считается урон.
dice_log = []
combat_log = []
dice_delay_ms = 80


def set_dice_delay(delay_ms):
    global dice_delay_ms

    dice_delay_ms = int(delay_ms)

    if dice_delay_ms < 0:
        dice_delay_ms = 0


def log_event(message):
    # Добавляем строку в лог боя.
    builtins.print(message)
    combat_log.append(str(message))

    if len(combat_log) > 12:
        while len(combat_log) > 12:
            combat_log.pop(0)


def dice_to_symbol(value):
    return f"D6:{value}"


def roll_d6():
    return random.randint(1, 6)


def morale_test(unit, models_lost=1):
    # Проверяем мораль отряда.
    roll = roll_d6()
    lost = models_lost

    if lost < 1:
        lost = 1

    needed = 2 + lost

    if needed > 6:
        needed = 6

    log_event(f"Мораль: {roll} (нужно {needed}+)")

    if roll < needed:
        unit.broken = True
        log_event("Мораль провалена!")
        return False
    else:
        log_event("Мораль успешна!")
        return True


def wound_roll_needed(strength, toughness):
    if strength >= toughness * 2:
        return 2

    if strength > toughness:
        return 3

    if strength == toughness:
        return 4

    if strength * 2 <= toughness:
        return 6

    return 5


def update_model_count(unit):
    # После урона пересчитываем, сколько моделей осталось.
    if unit.hp < 0:
        unit.hp = 0

    unit.models = (unit.hp + unit.hp_per_model - 1) // unit.hp_per_model

    if unit.models < 0:
        unit.models = 0


def model_ratio(unit):
    if hasattr(unit, "max_models"):
        max_models = unit.max_models
    else:
        max_models = unit.models

    if max_models < 1:
        max_models = 1

    models = unit.models

    if models < 0:
        models = 0

    return models / max_models


def scaled_attack_count(unit, base_attacks):
    # Если моделей стало меньше, атак тоже становится меньше.
    if unit.models <= 0:
        return 0

    attacks = int(base_attacks * model_ratio(unit))

    if attacks < base_attacks * model_ratio(unit):
        attacks += 1

    if attacks < 1:
        attacks = 1

    return attacks


def effective_weapon_attacks(unit):
    return scaled_attack_count(unit, unit.weapon.attacks)


def effective_melee_attacks(unit):
    return scaled_attack_count(unit, unit.melee_attacks)


def attack(attacker, target, waaagh=False):
    # Тут полностью считается стрельба.
    log_event("=== Стрельба ===")

    total_damage = 0
    bonus_attacks = 0
    base_attacks = effective_weapon_attacks(attacker)

    if waaagh:
        bonus_attacks += 1
        log_event("WAAAGH: бонусная атака!")

    distance_to_target = abs(attacker.x - target.x) + abs(attacker.y - target.y)

    if (
        "rapid_fire" in attacker.weapon.special_rules
        and distance_to_target <= attacker.weapon.weapon_range // 2
    ):
        bonus_attacks += base_attacks
        log_event("Быстрый огонь!")

    dice_log.clear()

    total_attacks = base_attacks + bonus_attacks
    log_event(f"Атак: {total_attacks}")

    for shot in range(total_attacks):
        log_event(f"Выстрел {shot + 1}")

        hit_roll = roll_d6()
        dice_log.append(("HIT", hit_roll))
        pygame.display.flip()
        pygame.time.delay(dice_delay_ms)

        log_event(f"Бросок попадания: {hit_roll}")

        extra_hits = 0

        if hit_roll == 6 and "sustained_hits" in attacker.weapon.special_rules:
            extra_hits += 1
            log_event("Доп. попадание!")

        if hit_roll < attacker.ballistic_skill:
            log_event("Промах!")
            continue

        log_event("Попадание!")

        for _ in range(1 + extra_hits):
            needed = wound_roll_needed(attacker.weapon.strength, target.toughness)
            wound_roll = roll_d6()
            dice_log.append(("WOUND", wound_roll))
            pygame.display.flip()
            pygame.time.delay(dice_delay_ms)

            log_event(f"Бросок ранения: {wound_roll} (нужно {needed}+)")

            if wound_roll < needed:
                log_event("Не ранил!")
                continue

            log_event("Ранение!")

            modified_save = target.armor_save - attacker.weapon.ap

            if is_in_cover(target):
                modified_save -= 1
                log_event("Цель в укрытии! +1 сейв")

            if modified_save > 6:
                modified_save = 6

            if modified_save < 2:
                modified_save = 2

            save_roll = roll_d6()
            dice_log.append(("SAVE", save_roll))
            pygame.display.flip()
            pygame.time.delay(dice_delay_ms)

            log_event(f"Сейв брони: {save_roll} (нужно {modified_save}+)")

            if save_roll >= modified_save:
                log_event("Спасено!")
                continue

            old_models = target.models
            target.hp -= attacker.weapon.damage
            update_model_count(target)

            if target.models < old_models:
                lost = old_models - target.models
                log_event(f"Потеряно моделей: {lost}")
                morale_test(target, lost)

            total_damage += attacker.weapon.damage
            log_event(f"Урон: {attacker.weapon.damage}")

    log_event(f"Всего урона: {total_damage}")
    log_event(f"HP цели: {target.hp}")


def melee_attack(attacker, target):
    # Тут считается ближний бой.
    log_event("=== Ближний бой ===")

    total_attacks = effective_melee_attacks(attacker)
    log_event(f"Атак в бою: {total_attacks}")

    for attack_num in range(total_attacks):
        log_event(f"Удар {attack_num + 1}")

        hit_roll = roll_d6()
        log_event(f"Бросок попадания: {hit_roll}")

        if hit_roll < attacker.melee_skill:
            log_event("Промах!")
            continue

        log_event("Попадание!")

        wound_needed = wound_roll_needed(attacker.melee_strength, target.toughness)
        wound_roll = roll_d6()
        log_event(f"Бросок ранения: {wound_roll}")

        if wound_roll < wound_needed:
            log_event("Не ранил!")
            continue

        save_roll = roll_d6()
        log_event(f"Бросок сейва: {save_roll}")

        if save_roll >= target.armor_save:
            log_event("Спасено!")
            continue

        old_models = target.models
        target.hp -= 1
        target.melee_flash = 15
        update_model_count(target)

        if target.models < old_models:
            lost = old_models - target.models
            log_event(f"Потеряно моделей: {lost}")
            morale_test(target, lost)

        log_event("Урон в ближнем бою!")


def attempt_charge(attacker, target):
    # Тут считается, получилось ли добежать до врага.
    from rules import distance, is_inside_grid, neighbors

    log_event("=== Натиск ===")

    charge_roll = roll_d6()
    log_event(f"Бросок натиска: {charge_roll}")

    charge_distance = distance(attacker.x, attacker.y, target.x, target.y)

    if charge_roll < charge_distance:
        log_event("Натиск провален!")
        return False

    log_event("Натиск успешен!")

    attacker.has_charged = True
    charge_tiles = []

    for tile in neighbors(target.x, target.y):
        tile_x, tile_y = tile

        if is_inside_grid(tile_x, tile_y):
            if not is_blocked(tile_x, tile_y):
                charge_tiles.append(tile)

    if charge_tiles:
        best_tile = None
        best_distance = None

        for tile in charge_tiles:
            tile_distance = distance(attacker.x, attacker.y, tile[0], tile[1])

            if best_tile is None or tile_distance < best_distance:
                best_tile = tile
                best_distance = tile_distance

        attacker.x, attacker.y = best_tile

    return True


def hit_chance(bs):
    success = 7 - bs
    return int((success / 6) * 100)


def wound_chance(strength, toughness):
    needed = wound_roll_needed(strength, toughness)
    success = 7 - needed
    return int((success / 6) * 100)


def save_chance(save):
    success = 7 - save
    return int((success / 6) * 100)


def is_engaged(unit, units):
    from rules import distance

    for other in units:
        if other == unit:
            continue

        if other.team == unit.team:
            continue

        if distance(unit.x, unit.y, other.x, other.y) <= 1:
            return True

    return False
