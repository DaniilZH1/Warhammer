from combat import log_event, roll_d6
from localization import role_label

# Тут меняется активная сторона и восстанавливаются сломанные отряды.

def recover_unit(unit):
    # Сломанный отряд пробует вернуться в бой.
    roll = roll_d6()
    needed = 4

    log_event(f"{role_label(unit.role)} Восстановление: {roll} (нужно {needed}+)")

    if roll < needed:
        unit.ap = 0
        unit.recovering = False
        log_event(f"{role_label(unit.role)} остается сломан")
        return False

    unit.broken = False
    unit.recovering = True
    unit.ap = unit.max_ap - 1

    if unit.ap < 0:
        unit.ap = 0

    log_event(f"{role_label(unit.role)} восстал: -1 AP")
    return True


def next_turn(current_team, units):
    # Меняем сторону: после 1 ходит 2, после 2 ходит 1.
    if current_team == 1:
        current_team = 2
    else:
        current_team = 1

    for unit in units:
        if unit.team != current_team:
            continue

        # В начале хода отряд снова получает AP и может действовать.
        unit.has_acted = False
        unit.acted_phases.clear()
        unit.has_charged = False
        unit.ap = unit.max_ap
        unit.recovering = False

        if unit.broken:
            recover_unit(unit)

    return current_team
