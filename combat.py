import random
from board import is_in_cover

dice_log = []

def dice_to_symbol(value):

    symbols = {
        1: "⚀",
        2: "⚁",
        3: "⚂",
        4: "⚃",
        5: "⚄",
        6: "⚅"
    }

    return f"D6:{value}"

def roll_d6():
    return random.randint(1, 6)

def wound_roll_needed(strength, toughness):

    if strength >= toughness * 2:
        return 2

    elif strength > toughness:
        return 3

    elif strength == toughness:
        return 4

    elif strength * 2 <= toughness:
        return 6

    else:
        return 5

def attack(attacker, target):

    print("\n=== ATTACK ===")

    total_damage = 0

    global dice_log

    dice_log.clear()

    for shot in range(attacker.weapon.attacks):

        print(f"\nSHOT {shot + 1}")

        # HIT ROLL
        hit_roll = roll_d6()

        dice_log.append(
            ("HIT", hit_roll)
        )

        print(f"Hit roll: {hit_roll}")

        if hit_roll < attacker.ballistic_skill:

            print("MISS!")
            continue

        print("HIT!")

        # WOUND ROLL
        needed = wound_roll_needed(
            attacker.weapon.strength,
            target.toughness
        )

        wound_roll = roll_d6()

        dice_log.append(
            ("WOUND", wound_roll)
        )

        print(
            f"Wound roll: "
            f"{wound_roll} "
            f"(need {needed}+)"
        )

        if wound_roll < needed:

            print("FAILED TO WOUND!")
            continue

        print("WOUND!")

        # ARMOR SAVE
        modified_save = (
            target.armor_save
            - attacker.weapon.ap
        )

        # COVER BONUS
        if is_in_cover(target):

            modified_save -= 1

            print("TARGET IN COVER! +1 SAVE")

        modified_save = min(modified_save, 6)
        modified_save = max(modified_save, 2)

        save_roll = roll_d6()

        dice_log.append(
            ("SAVE", save_roll)
        )

        print(
            f"Armor save: "
            f"{save_roll} "
            f"(need {modified_save}+)"
        )

        if save_roll >= modified_save:

            print("SAVED!")
            continue

        # DAMAGE
        target.hp -= attacker.weapon.damage
        
        new_models = max(
            0,
            target.hp // target.hp_per_model
        )

        if target.hp % target.hp_per_model > 0:
            new_models += 1

        if new_models < target.models:

            lost = target.models - new_models

            print(
                f"{lost} MODEL LOST!"
            )

        target.models = new_models
        
        total_damage += attacker.weapon.damage

        print(
            f"DAMAGE: "
            f"{attacker.weapon.damage}"
        )

    print(f"\nTOTAL DAMAGE: {total_damage}")
    print(f"TARGET HP: {target.hp}")

def hit_chance(bs):

    success = 7 - bs

    return int((success / 6) * 100)

def wound_chance(strength, toughness):

    needed = wound_roll_needed(
        strength,
        toughness
    )

    success = 7 - needed

    return int((success / 6) * 100)

def save_chance(save):

    success = 7 - save

    return int((success / 6) * 100)