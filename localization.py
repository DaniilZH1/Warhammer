# Тут собраны переводы текста, который показывается игроку.
phase_labels = {
    "MOVEMENT": "Движение",
    "SHOOTING": "Стрельба",
    "CHARGE": "Натиск",
    "FIGHT": "Бой",
}

role_labels = {
    "plasma": "Плазма",
    "tactical": "Тактики",
    "assault": "Штурм",
    "heavy": "Тяжелые",
    "boyz": "Бойзы",
    "shoota": "Стрелки",
    "nob": "Ноб",
    "rokkit": "Роккит",
}

role_short_labels = {
    "plasma": "Пла",
    "tactical": "Так",
    "assault": "Штм",
    "heavy": "Тяж",
    "boyz": "Бой",
    "shoota": "Стр",
    "nob": "Ноб",
    "rokkit": "Рок",
}

faction_labels = {
    "marines": "Космодесант",
    "orks": "Орки",
}

team_labels = {
    1: "Космодесант",
    2: "Орки",
}

objective_labels = {
    "LEFT": "Лев",
    "CENTER": "Цен",
    "RIGHT": "Прав",
}

status_labels = {
    "BROKEN": "Слом",
    "RECOVER": "Встал",
    "WAIT": "Ждет",
    "DONE": "Ходил",
    "LOW AP": "Мало AP",
    "READY": "Готов",
}

hint_labels = {
    "SELECT UNIT": "Выбери",
    "BROKEN": "Сломан",
    "NOT ENOUGH AP": "Мало AP",
    "DONE THIS PHASE": "Уже ходил",
    "OCCUPIED": "Занято",
    "BLOCKED": "Преграда",
    "MOVE": "Идти",
    "OUT OF MOVE": "Далеко",
    "SELECT TARGET": "Выбери цель",
    "ALLY": "Свой",
    "ENGAGED": "В бою",
    "OUT OF RANGE": "Далеко",
    "NO LOS": "Нет обзора",
    "SHOOT": "Стрелять",
    "CHARGE": "Натиск",
    "OUT OF CHARGE": "Далеко",
    "FIGHT": "Драться",
    "OUT OF MELEE": "Не достать",
}

dice_labels = {
    "HIT": "Поп",
    "WOUND": "Ран",
    "SAVE": "Сейв",
}

weapon_labels = {
    "Bolter": "Болтер",
    "Plasma Gun": "Плазма",
    "Heavy Bolter": "Тяж. болтер",
    "Bolt Pistol": "Болт-пистолет",
    "Shoota": "Шута",
    "Slugga": "Слагга",
    "Rokkit Launcha": "Роккит",
}


def phase_label(phase):
    if phase in phase_labels:
        return phase_labels[phase]

    return str(phase)


def role_label(role):
    if role in role_labels:
        return role_labels[role]

    return str(role)


def role_short_label(role):
    if role in role_short_labels:
        return role_short_labels[role]

    return str(role)[:3].upper()


def faction_label(faction):
    if faction in faction_labels:
        return faction_labels[faction]

    return str(faction)


def team_label(team):
    if team in team_labels:
        return team_labels[team]

    return f"Команда {team}"


def objective_label(name):
    if name in objective_labels:
        return objective_labels[name]

    return str(name)


def status_label(status):
    if status in status_labels:
        return status_labels[status]

    return str(status)


def hint_label(hint):
    if hint in hint_labels:
        return hint_labels[hint]

    return str(hint)


def dice_label(label):
    if label in dice_labels:
        return dice_labels[label]

    return str(label)


def weapon_label(name):
    if name in weapon_labels:
        return weapon_labels[name]

    return str(name)
