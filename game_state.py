from combat import combat_log, dice_log, log_event
from board import objective_zones
from effects import add_vp_text
from localization import objective_label, team_label
from rules import objective_control
from turn_manager import next_turn
from unit import Unit

# Главные числа для партии.
victory_points = 6
charge_max_range = 6
ai_turn_delay_ms = 700
ai_charge_comfort_range = 4

# В коде фазы на английском, а на экране они переводятся.
phases = [
    "MOVEMENT",
    "SHOOTING",
    "CHARGE",
    "FIGHT",
]


def create_units():
    # Тут создаются отряды в начале игры.
    units = []

    units.append(Unit(1, 1, 1, "marines", "plasma"))
    units.append(Unit(1, 3, 1, "marines", "tactical"))
    units.append(Unit(2, 1, 1, "marines", "assault"))
    units.append(Unit(2, 3, 1, "marines", "heavy"))

    units.append(Unit(8, 8, 2, "orks", "boyz"))
    units.append(Unit(8, 6, 2, "orks", "shoota"))
    units.append(Unit(7, 8, 2, "orks", "nob"))
    units.append(Unit(7, 6, 2, "orks", "rokkit"))

    return units


class GameState:
    # Тут хранится состояние текущей партии.
    def __init__(self, ai_orks_enabled=False):
        self.ai_orks_enabled = ai_orks_enabled
        self.reset(ai_orks_enabled=ai_orks_enabled, log=False)

    def reset(self, ai_orks_enabled=None, log=True):
        # Сбрасываем игру в начало.
        if ai_orks_enabled is not None:
            self.ai_orks_enabled = ai_orks_enabled

        self.units = create_units()
        self.selected_unit = None
        self.hovered_target = None
        self.current_team = 1
        self.marine_vp = 0
        self.ork_vp = 0
        self.winner = None
        self.victory_reason = None
        self.turn_number = 1
        self.phase_num = 0
        self.current_phase = phases[self.phase_num]
        self.waaagh_active = False
        self.waaagh_used = False
        self.full_log_visible = False
        self.help_visible = False
        self.ai_timer = 0
        self.floating_texts = []
        self.effects = []
        combat_log.clear()
        dice_log.clear()

        if log:
            log_event("Новая игра")
            log_event("Ход 1: Космодесант")

    def remove_dead_units(self):
        # Убираем мертвые отряды с поля.
        old_units = list(self.units)

        for unit in old_units:
            if unit.hp <= 0 or unit.models <= 0:
                self.units.remove(unit)

    def check_victory(self):
        # Проверяем, победил ли кто-нибудь.
        teams_alive = {unit.team for unit in self.units}

        if len(teams_alive) == 1:
            self.winner = teams_alive.pop()
            self.victory_reason = "wipe"
            if self.winner == 1:
                winner_name = "Космодесант"
            else:
                winner_name = "Орки"
            log_event(f"{winner_name}: Победа разгромом!")
            return

        if self.marine_vp >= victory_points:
            self.winner = 1
            self.victory_reason = "vp"
            log_event("Космодесант: победа по очкам!")
        elif self.ork_vp >= victory_points:
            self.winner = 2
            self.victory_reason = "vp"
            log_event("Орки: победа по очкам!")

    def mark_phase_action(self, unit):
        # Запоминаем, что отряд уже ходил в этой фазе.
        unit.acted_phases.add(self.current_phase)
        unit.has_acted = True

    def score_current_turn_objectives(self):
        # В начале хода даем очки за захваченные точки.
        controlled = 0

        for zone in objective_zones:
            status = objective_control(self.units, zone)

            if status["controller"] == self.current_team:
                controlled += 1
                add_vp_text(self, zone, self.current_team, 1)
                log_event(f"Взята точка: {objective_label(zone['name'])}")

        if controlled <= 0:
            return

        if self.current_team == 1:
            self.marine_vp += controlled
            log_event(f"Космодесант получает {controlled} Поб!")
        else:
            self.ork_vp += controlled
            log_event(f"Орки получают {controlled} Поб!")

        self.check_victory()

    def advance_phase(self):
        # Переключаем фазу. После боя ходит другая сторона.
        self.selected_unit = None

        if self.winner:
            return

        if self.current_phase == "FIGHT":
            self.phase_num = 0
            self.current_team = next_turn(self.current_team, self.units)
            self.waaagh_active = False
            self.current_phase = phases[self.phase_num]
            if self.current_team == 1:
                self.turn_number += 1
            log_event(f"Ход {self.turn_number}: {team_label(self.current_team)}")
            self.score_current_turn_objectives()
        else:
            self.phase_num += 1
            self.current_phase = phases[self.phase_num]

        from localization import phase_label

        log_event(f"Фаза: {phase_label(self.current_phase)}")

    def activate_waaagh(self):
        # WAAAGH - одноразовый бонус орков.
        if self.current_team != 2:
            log_event("WAAAGH доступен только оркам!")
            return False

        if self.waaagh_used:
            log_event("WAAAGH уже использован!")
            return False

        self.waaagh_active = True
        self.waaagh_used = True
        log_event("WAAAAAGH!!!")
        return True
