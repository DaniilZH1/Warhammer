from board import hex_center
from settings import white

# Тут только красивые эффекты. На правила они не влияют.

class ShotEffect:
    def __init__(self, attacker, target, color=(255, 220, 80), lifetime=10):
        self.start = hex_center(attacker.x, attacker.y)
        self.end = hex_center(target.x, target.y)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self):
        self.lifetime -= 1

    def draw(self, screen, font):
        import pygame

        # Линия выстрела постепенно пропадает.
        alpha_ratio = self.lifetime / self.max_lifetime

        if alpha_ratio < 0:
            alpha_ratio = 0

        red = int(self.color[0] * alpha_ratio)
        green = int(self.color[1] * alpha_ratio)
        blue = int(self.color[2] * alpha_ratio)
        color = (red, green, blue)
        width = int(5 * alpha_ratio)

        if width < 1:
            width = 1

        circle_size = int(8 * alpha_ratio)

        if circle_size < 2:
            circle_size = 2

        pygame.draw.line(screen, color, self.start, self.end, width)
        pygame.draw.circle(screen, color, self.end, circle_size)


class MeleeEffect:
    def __init__(self, unit, color=(255, 90, 50), lifetime=14):
        self.center = hex_center(unit.x, unit.y)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self):
        self.lifetime -= 1

    def draw(self, screen, font):
        import pygame

        # Круг показывает удар в ближнем бою.
        alpha_ratio = self.lifetime / self.max_lifetime

        if alpha_ratio < 0:
            alpha_ratio = 0

        red = int(self.color[0] * alpha_ratio)
        green = int(self.color[1] * alpha_ratio)
        blue = int(self.color[2] * alpha_ratio)
        color = (red, green, blue)
        radius = int(22 * (1 - alpha_ratio) + 8)
        pygame.draw.circle(screen, color, self.center, radius, 3)
        pygame.draw.line(
            screen,
            color,
            (self.center[0] - radius, self.center[1] - radius // 2),
            (self.center[0] + radius, self.center[1] + radius // 2),
            3,
        )


class FloatingText:
    def __init__(self, x, y, text, color=(255, 80, 80), lifetime=45):
        self.x, self.y = hex_center(x, y)
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self):
        # Текст урона медленно летит вверх.
        self.y -= 0.6
        self.lifetime -= 1

    def draw(self, screen, font):
        alpha_ratio = self.lifetime / self.max_lifetime

        if alpha_ratio < 0:
            alpha_ratio = 0

        red = int(self.color[0] * alpha_ratio)
        green = int(self.color[1] * alpha_ratio)
        blue = int(self.color[2] * alpha_ratio)
        color = (red, green, blue)

        if color == (0, 0, 0):
            color = white

        rendered = font.render(self.text, True, color)
        screen.blit(
            rendered,
            (
                self.x - rendered.get_width() // 2,
                self.y - rendered.get_height() // 2,
            ),
        )


def add_damage_text(state, unit, damage):
    if damage <= 0:
        return

    state.floating_texts.append(
        FloatingText(unit.x, unit.y, f"-{damage}")
    )


def add_shot_effect(state, attacker, target):
    state.effects.append(ShotEffect(attacker, target))


def add_melee_effect(state, target):
    state.effects.append(MeleeEffect(target))


def add_vp_text(state, zone, team, points):
    # Текст очков победы показываем над точкой.
    if points <= 0:
        return

    if team == 1:
        color = (100, 180, 255)
    else:
        color = (100, 255, 100)

    text = FloatingText(0, 0, f"+{points} VP", color=color, lifetime=70)
    total_x = 0
    total_y = 0

    for x, y in zone["tiles"]:
        center_x, center_y = hex_center(x, y)
        total_x += center_x
        total_y += center_y

    text.x = total_x / len(zone["tiles"])
    text.y = total_y / len(zone["tiles"])
    state.floating_texts.append(text)


def update_floating_texts(state):
    old_texts = list(state.floating_texts)

    for text in old_texts:
        text.update()

        if text.lifetime <= 0:
            state.floating_texts.remove(text)


def draw_floating_texts(screen, font, state):
    for text in state.floating_texts:
        text.draw(screen, font)


def update_effects(state):
    old_effects = list(state.effects)

    for effect in old_effects:
        effect.update()

        if effect.lifetime <= 0:
            state.effects.remove(effect)


def draw_effects(screen, font, state):
    for effect in state.effects:
        effect.draw(screen, font)
