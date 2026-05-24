def next_turn(current_team, units):

    current_team = 2 if current_team == 1 else 1

    for unit in units:

        if unit.team == current_team:
            unit.has_acted = False
            unit.ap

    return current_team
