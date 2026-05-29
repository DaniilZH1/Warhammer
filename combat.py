import random
import builtins

import pygame

from board import is_in_cover

dice_log = []
combat_log = []


def log_event(message):
    builtins.print(message)
    combat_log.append(str(message))

    if len(combat_log) > 12:
        del combat_log[:-12]


def dice_to_symbol(value):
    return f"D6:{value}"


def roll_d6():
    return random.randint(1, 6)


def morale_test(unit):
    roll = roll_d6()

    log_event(f"MORALE TEST: {roll}")

    if roll <= 2:
        unit.broken = True
        log_event("MORALE FAILED!")
    else:
        log_event("MORALE PASSED!")


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
    unit.hp = max(0, unit.hp)
    unit.models = max(
        0,
        (unit.hp + unit.hp_per_model - 1) // unit.hp_per_model,
    )


def attack(attacker, target, waaagh=False):
    log_event("=== ATTACK ===")

    total_damage = 0
    bonus_attacks = 0

    if waaagh:
        bonus_attacks += 1
        log_event("WAAAGH BONUS ATTACK!")

    distance_to_target = abs(attacker.x - target.x) + abs(attacker.y - target.y)

    if (
        "rapid_fire" in attacker.weapon.special_rules
        and distance_to_target <= attacker.weapon.weapon_range // 2
    ):
        bonus_attacks += attacker.weapon.attacks
        log_event("RAPID FIRE!")

    dice_log.clear()

    total_attacks = attacker.weapon.attacks + bonus_attacks

    for shot in range(total_attacks):
        log_event(f"SHOT {shot + 1}")

        hit_roll = roll_d6()
        dice_log.append(("HIT", hit_roll))
        pygame.display.flip()
        pygame.time.delay(300)

        log_event(f"Hit roll: {hit_roll}")

        extra_hits = 0

        if hit_roll == 6 and "sustained_hits" in attacker.weapon.special_rules:
            extra_hits += 1
            log_event("SUSTAINED HIT!")

        if hit_roll < attacker.ballistic_skill:
            log_event("MISS!")
            continue

        log_event("HIT!")

        for _ in range(1 + extra_hits):
            needed = wound_roll_needed(attacker.weapon.strength, target.toughness)
            wound_roll = roll_d6()
            dice_log.append(("WOUND", wound_roll))
            pygame.display.flip()
            pygame.time.delay(300)

            log_event(f"Wound roll: {wound_roll} (need {needed}+)")

            if wound_roll < needed:
                log_event("FAILED TO WOUND!")
                continue

            log_event("WOUND!")

            modified_save = target.armor_save - attacker.weapon.ap

            if is_in_cover(target):
                modified_save -= 1
                log_event("TARGET IN COVER! +1 SAVE")

            modified_save = min(modified_save, 6)
            modified_save = max(modified_save, 2)

            save_roll = roll_d6()
            dice_log.append(("SAVE", save_roll))
            pygame.display.flip()
            pygame.time.delay(300)

            log_event(f"Armor save: {save_roll} (need {modified_save}+)")

            if save_roll >= modified_save:
                log_event("SAVED!")
                continue

            old_models = target.models
            target.hp -= attacker.weapon.damage
            update_model_count(target)

            if target.models < old_models:
                lost = old_models - target.models
                log_event(f"{lost} MODEL LOST!")
                morale_test(target)

            total_damage += attacker.weapon.damage
            log_event(f"DAMAGE: {attacker.weapon.damage}")

    log_event(f"TOTAL DAMAGE: {total_damage}")
    log_event(f"TARGET HP: {target.hp}")


def melee_attack(attacker, target):
    log_event("=== MELEE ATTACK ===")

    for attack_num in range(attacker.melee_attacks):
        log_event(f"MELEE HIT {attack_num + 1}")

        hit_roll = roll_d6()
        log_event(f"Hit roll: {hit_roll}")

        if hit_roll < attacker.melee_skill:
            log_event("MISS!")
            continue

        log_event("HIT!")

        wound_needed = wound_roll_needed(4, target.toughness)
        wound_roll = roll_d6()
        log_event(f"Wound roll: {wound_roll}")

        if wound_roll < wound_needed:
            log_event("FAILED TO WOUND!")
            continue

        save_roll = roll_d6()
        log_event(f"Save roll: {save_roll}")

        if save_roll >= target.armor_save:
            log_event("SAVED!")
            continue

        old_models = target.models
        target.hp -= 1
        target.melee_flash = 15
        update_model_count(target)

        if target.models < old_models:
            morale_test(target)

        log_event("MELEE DAMAGE!")


def attempt_charge(attacker, target):
    log_event("=== CHARGE ===")

    charge_roll = roll_d6()
    log_event(f"Charge roll: {charge_roll}")

    distance = abs(attacker.x - target.x) + abs(attacker.y - target.y)

    if charge_roll < distance:
        log_event("CHARGE FAILED!")
        return False

    log_event("CHARGE SUCCESS!")

    attacker.has_charged = True

    if attacker.x < target.x:
        attacker.x = target.x - 1
        attacker.y = target.y
    elif attacker.x > target.x:
        attacker.x = target.x + 1
        attacker.y = target.y
    elif attacker.y < target.y:
        attacker.y = target.y - 1
        attacker.x = target.x
    elif attacker.y > target.y:
        attacker.y = target.y + 1
        attacker.x = target.x

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
    for other in units:
        if other == unit:
            continue

        if other.team == unit.team:
            continue

        distance = abs(unit.x - other.x) + abs(unit.y - other.y)

        if distance <= 1:
            return True

    return False
