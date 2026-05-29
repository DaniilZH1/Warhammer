def next_turn(current_team, units):
    current_team = 2 if current_team == 1 else 1

    for unit in units:
        if unit.team != current_team:
            continue

        unit.has_acted = False
        unit.acted_phases.clear()
        unit.has_charged = False
        unit.ap = unit.max_ap

        if unit.broken:
            unit.ap = max(0, unit.ap - 1)
            print("BROKEN: -1 AP")

        unit.broken = False

    return current_team
