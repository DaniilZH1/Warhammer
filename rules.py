from combat import is_engaged
from board import is_blocked, objective_tiles, objective_zones
from settings import grid_size

# Тут лежат правила игры. Экран тут не рисуется.

def distance(x1, y1, x2, y2):
    # Считаем расстояние между двумя гексами.
    q1, r1 = offset_to_axial(x1, y1)
    q2, r2 = offset_to_axial(x2, y2)

    return (
        abs(q1 - q2)
        + abs(q1 + r1 - q2 - r2)
        + abs(r1 - r2)
    ) // 2


def offset_to_axial(x, y):
    return x, y - (x - (x & 1)) // 2


def axial_to_offset(q, r):
    return q, r + (q - (q & 1)) // 2


def current_action_cost(phase):
    # Натиск стоит 2 AP, остальные действия стоят 1 AP.
    if phase == "CHARGE":
        return 2

    return 1


def get_unit_at(units, x, y):
    for unit in units:
        if unit.x == x and unit.y == y:
            return unit

    return None


def is_inside_grid(x, y):
    return 0 <= x < grid_size and 0 <= y < grid_size


def neighbors(x, y):
    # Для четных и нечетных колонок соседи разные.
    if x % 2:
        return [
            (x + 1, y + 1),
            (x + 1, y),
            (x, y - 1),
            (x - 1, y),
            (x - 1, y + 1),
            (x, y + 1),
        ]

    return [
        (x + 1, y),
        (x + 1, y - 1),
        (x, y - 1),
        (x - 1, y - 1),
        (x - 1, y),
        (x, y + 1),
    ]


def reachable_tiles(unit, units):
    # Ищем все клетки, куда отряд может дойти.
    occupied_tiles = {
        (other.x, other.y)
        for other in units
        if other != unit
    }
    start = (unit.x, unit.y)
    visited = {start}
    frontier = [(start, 0)]
    reachable = {start}

    while frontier:
        (x, y), cost = frontier.pop(0)

        if cost >= unit.move_range:
            continue

        for next_x, next_y in neighbors(x, y):
            tile = (next_x, next_y)

            if tile in visited:
                continue

            visited.add(tile)

            if not is_inside_grid(next_x, next_y):
                continue

            if tile in occupied_tiles or is_blocked(next_x, next_y):
                continue

            reachable.add(tile)
            frontier.append((tile, cost + 1))

    return reachable


def cube_round(q, r):
    # Это нужно, чтобы нормально проверить линию стрельбы.
    x = q
    z = r
    y = -x - z

    rounded_x = round(x)
    rounded_y = round(y)
    rounded_z = round(z)

    diff_x = abs(rounded_x - x)
    diff_y = abs(rounded_y - y)
    diff_z = abs(rounded_z - z)

    if diff_x > diff_y and diff_x > diff_z:
        rounded_x = -rounded_y - rounded_z
    elif diff_y > diff_z:
        rounded_y = -rounded_x - rounded_z
    else:
        rounded_z = -rounded_x - rounded_y

    return rounded_x, rounded_z


def line_tiles(x1, y1, x2, y2):
    # Возвращает клетки между стрелком и целью.
    start_q, start_r = offset_to_axial(x1, y1)
    end_q, end_r = offset_to_axial(x2, y2)
    steps = distance(x1, y1, x2, y2)

    if steps <= 1:
        return []

    tiles = []

    for index in range(1, steps):
        progress = index / steps
        q = start_q + (end_q - start_q) * progress
        r = start_r + (end_r - start_r) * progress
        tile = axial_to_offset(*cube_round(q, r))

        if tile not in tiles:
            tiles.append(tile)

    return tiles


def has_line_of_sight_between(x1, y1, x2, y2):
    for x, y in line_tiles(x1, y1, x2, y2):
        if is_blocked(x, y):
            return False

    return True


def has_line_of_sight(attacker, target):
    return has_line_of_sight_between(attacker.x, attacker.y, target.x, target.y)


def unit_can_act(unit, phase):
    return (
        not unit.broken
        and unit.ap >= current_action_cost(phase)
        and phase not in unit.acted_phases
    )


def ready_units(units, team, phase):
    result = []

    for unit in units:
        if unit.team == team:
            if unit_can_act(unit, phase):
                result.append(unit)

    return result


def unit_action_status(unit, current_team, phase):
    # Возвращает статус отряда для надписи на поле.
    if unit.broken:
        return ("BROKEN", (150, 50, 150))

    if unit.recovering:
        return ("RECOVER", (150, 120, 40))

    if unit.team != current_team:
        return ("WAIT", (80, 80, 80))

    if phase in unit.acted_phases:
        return ("DONE", (90, 90, 90))

    if unit.ap < current_action_cost(phase):
        return ("LOW AP", (150, 110, 40))

    return ("READY", (50, 150, 80))


def can_move_to(unit, x, y, units):
    return (x, y) in reachable_tiles(unit, units)


def can_shoot_target(unit, target, units):
    return (
        target
        and target.team != unit.team
        and not is_engaged(unit, units)
        and distance(unit.x, unit.y, target.x, target.y) <= unit.weapon.weapon_range
        and has_line_of_sight(unit, target)
    )


def can_charge_target(unit, target, charge_max_range):
    return (
        target
        and target.team != unit.team
        and distance(unit.x, unit.y, target.x, target.y) <= charge_max_range
    )


def can_fight_target(unit, target):
    return (
        target
        and target.team != unit.team
        and distance(unit.x, unit.y, target.x, target.y) <= 1
    )


def action_hint(unit, target, x, y, phase, units, charge_max_range):
    # Возвращает подсказку для панели действия.
    if not unit:
        return "SELECT UNIT"

    if unit.broken:
        return "BROKEN"

    if unit.ap < current_action_cost(phase):
        return "NOT ENOUGH AP"

    if phase in unit.acted_phases:
        return "DONE THIS PHASE"

    if phase == "MOVEMENT":
        if target:
            return "OCCUPIED"

        if is_blocked(x, y):
            return "BLOCKED"

        if can_move_to(unit, x, y, units):
            return "MOVE"

        return "OUT OF MOVE"

    if not target:
        return "SELECT TARGET"

    if target.team == unit.team:
        return "ALLY"

    if phase == "SHOOTING":
        if is_engaged(unit, units):
            return "ENGAGED"

        if distance(unit.x, unit.y, target.x, target.y) > unit.weapon.weapon_range:
            return "OUT OF RANGE"

        if not has_line_of_sight(unit, target):
            return "NO LOS"

        return "SHOOT"

    if phase == "CHARGE":
        if can_charge_target(unit, target, charge_max_range):
            return "CHARGE"

        return "OUT OF CHARGE"

    if phase == "FIGHT":
        if can_fight_target(unit, target):
            return "FIGHT"

        return "OUT OF MELEE"

    return ""


def count_objective_control(units, team, tiles=None):
    # Контроль точки = количество моделей умножить на OC.
    tiles = tiles or objective_tiles
    total = 0

    for unit in units:
        if unit.team != team:
            continue

        if (unit.x, unit.y) in tiles:
            total += unit.models * unit.oc

    return total


def objective_control(units, zone):
    marine_control = count_objective_control(units, 1, zone["tiles"])
    ork_control = count_objective_control(units, 2, zone["tiles"])
    controller = None

    if marine_control > ork_control:
        controller = 1
    elif ork_control > marine_control:
        controller = 2

    return {
        "name": zone["name"],
        "marine": marine_control,
        "ork": ork_control,
        "controller": controller,
    }


def objective_statuses(units):
    result = []

    for zone in objective_zones:
        result.append(objective_control(units, zone))

    return result


def controlled_objective_count(units, team):
    count = 0
    statuses = objective_statuses(units)

    for status in statuses:
        if status["controller"] == team:
            count += 1

    return count
