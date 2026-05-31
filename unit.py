import pygame

from board import hex_center
from settings import *
from sprite_loader import load_unit_sprite
from weapon import (
    bolter,
    bolt_pistol,
    heavy_bolter,
    plasma_gun,
    rokkit_launcha,
    shoota,
    slugga,
)

# Буквы на отрядах, чтобы было понятно кто есть кто.
role_badges = {
    "plasma": "P",
    "tactical": "T",
    "assault": "A",
    "heavy": "H",
    "boyz": "B",
    "shoota": "S",
    "nob": "N",
    "rokkit": "R",
}


class Unit:
    # Класс одного отряда на поле.
    def __init__(self, x, y, team, faction, role=None):
        self.x = x
        self.y = y
        self.team = team
        self.faction = faction

        if role:
            self.role = role
        else:
            self.role = faction

        if faction == "marines":
            # Базовые параметры космодесанта.
            self.models = 5
            self.hp_per_model = 2
            self.max_ap = 3
            self.ballistic_skill = 3
            self.toughness = 4
            self.armor_save = 3
            self.oc = 3
            self.melee_attacks = 2
            self.melee_skill = 3
            self.melee_strength = 4
            if role == "plasma":
                self.weapon = plasma_gun
            elif role is None and x == 1 and y == 1:
                self.weapon = plasma_gun
            elif role == "assault":
                self.models = 4
                self.oc = 2
                self.move_range = 3
                self.melee_attacks = 5
                self.melee_skill = 2
                self.weapon = bolt_pistol
            elif role == "heavy":
                self.models = 3
                self.oc = 1
                self.move_range = 1
                self.melee_attacks = 1
                self.weapon = heavy_bolter
            else:
                self.weapon = bolter
                
        elif faction == "orks":
            # Базовые параметры орков.
            self.models = 10
            self.hp_per_model = 1
            self.max_ap = 2
            self.ballistic_skill = 5
            self.toughness = 5
            self.armor_save = 5
            self.oc = 1
            self.melee_attacks = 4
            self.melee_skill = 4
            self.melee_strength = 4
            self.weapon = shoota
            if role == "boyz":
                self.models = 12
                self.oc = 1
                self.weapon = slugga
                self.melee_attacks = 5
            elif role == "nob":
                self.models = 4
                self.oc = 1
                self.hp_per_model = 2
                self.armor_save = 4
                self.melee_attacks = 6
                self.melee_skill = 3
                self.melee_strength = 5
                self.weapon = slugga
            elif role == "rokkit":
                self.models = 5
                self.oc = 1
                self.melee_attacks = 2
                self.weapon = rokkit_launcha
        else:
            raise ValueError(f"Unknown faction: {faction}")

        self.max_models = self.models
        self.hp = self.models * self.hp_per_model
        if hasattr(self, "move_range"):
            pass
        else:
            self.move_range = 2

        self.has_acted = False
        self.acted_phases = set()
        self.has_charged = False
        self.broken = False
        self.recovering = False
        self.melee_flash = 0
        self.move_animation = None

        self.ap = self.max_ap

    def start_move_animation(self, from_x, from_y, to_x, to_y, frames=14):
        # Запускаем простую анимацию движения.
        if frames < 1:
            frames = 1

        self.move_animation = {
            "from": hex_center(from_x, from_y),
            "to": hex_center(to_x, to_y),
            "frame": 0,
            "frames": frames,
        }

    def current_center(self):
        # Возвращаем текущую точку, где надо рисовать отряд.
        if not self.move_animation:
            return hex_center(self.x, self.y)

        frame = self.move_animation["frame"]
        frames = self.move_animation["frames"]
        progress = frame / frames

        if progress > 1:
            progress = 1

        eased = 1 - (1 - progress) * (1 - progress)
        from_x, from_y = self.move_animation["from"]
        to_x, to_y = self.move_animation["to"]

        return (
            int(from_x + (to_x - from_x) * eased),
            int(from_y + (to_y - from_y) * eased),
        )

    def update_animation(self):
        if not self.move_animation:
            return

        self.move_animation["frame"] += 1

        if self.move_animation["frame"] >= self.move_animation["frames"]:
            self.move_animation = None

    def draw(
        self,
        screen,
        font,
        selected=False,
        hovered=False,
        engaged=False,
        action_status=None,
        status_font=None,
    ):
        # Рисуем отряд и все кружки/подписи вокруг него.
        center = self.current_center()

        if hovered:
            pygame.draw.circle(
                screen,
                (255, 255, 0),
                center,
                hex_size - 2,
                4,
            )

        if selected:
            pygame.draw.circle(
                screen,
                green,
                center,
                hex_size - 6,
                4,
            )

        if engaged:
            pygame.draw.circle(
                screen,
                (255, 120, 0),
                center,
                hex_size - 12,
                3,
            )

        if self.melee_flash > 0:
            pygame.draw.circle(
                screen,
                (255, 0, 0),
                center,
                hex_size - 6,
            )

            self.melee_flash -= 1

        if status_font:
            real_status_font = status_font
        else:
            real_status_font = font

        self.draw_sprite(screen, center, font, real_status_font)

        if self.broken:
            pygame.draw.circle(
                screen,
                (255, 0, 255),
                center,
                hex_size // 2 + 6,
                3,
            )

        if self.recovering:
            pygame.draw.circle(
                screen,
                (255, 220, 80),
                center,
                hex_size // 2 + 10,
                3,
            )

        hp_text = font.render(str(self.hp), True, white)
        screen.blit(
            hp_text,
            (
                center[0] - hex_size // 2,
                center[1] - hex_size // 2,
            ),
        )

        if action_status and status_font:
            label, label_color = action_status
            label_text = status_font.render(label, True, white)
            label_width = label_text.get_width() + 8

            if label_width < 46:
                label_width = 46

            label_rect = pygame.Rect(
                center[0] - label_width // 2,
                center[1] + hex_size // 2 - 8,
                label_width,
                16,
            )

            pygame.draw.rect(screen, label_color, label_rect, border_radius=3)
            pygame.draw.rect(screen, black, label_rect, 1, border_radius=3)
            screen.blit(
                label_text,
                (
                    label_rect.centerx - label_text.get_width() // 2,
                    label_rect.centery - label_text.get_height() // 2,
                ),
            )

        self.update_animation()

    def draw_sprite(self, screen, center, font, badge_font):
        # Если есть PNG, рисуем его. Если нет, рисуем простой спрайт сами.
        external_sprite = load_unit_sprite(self.faction, self.role)

        if external_sprite:
            self.blit_loaded_sprite(screen, external_sprite, center)
        elif self.faction == "marines":
            self.draw_marine_sprite(screen, center)
        else:
            self.draw_ork_sprite(screen, center)

        self.draw_role_badge(screen, center, badge_font)
        self.draw_model_pips(screen, center)

    def blit_loaded_sprite(self, screen, sprite, center):
        rect = sprite.get_rect(center=(center[0], center[1] - 5))
        shadow = pygame.Surface((46, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        screen.blit(shadow, (center[0] - 23, center[1] + 18))
        screen.blit(sprite, rect)

    def draw_marine_sprite(self, screen, center, include_shadow=True):
        # Простой спрайт космодесанта из прямоугольников.
        red = (188, 42, 42)
        red_dark = (88, 24, 28)
        red_light = (235, 86, 70)
        black = (28, 26, 24)
        metal = (150, 150, 138)
        visor = (100, 210, 245)
        plasma = (82, 235, 245)
        gold = (232, 194, 80)

        sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.draw_px(sprite, black, 9, 27, 14, 2)
        self.draw_px(sprite, red_dark, 11, 19, 4, 8)
        self.draw_px(sprite, red_dark, 18, 19, 4, 8)
        self.draw_px(sprite, red, 12, 13, 9, 10)
        self.draw_px(sprite, red_dark, 10, 14, 4, 7)
        self.draw_px(sprite, red_dark, 20, 14, 4, 7)
        self.draw_px(sprite, red_light, 9, 11, 5, 5)
        self.draw_px(sprite, red_light, 20, 11, 5, 5)
        self.draw_px(sprite, red_dark, 12, 6, 10, 8)
        self.draw_px(sprite, red, 13, 5, 8, 7)
        self.draw_px(sprite, visor, 14, 8, 6, 2)
        self.draw_px(sprite, red_light, 14, 15, 2, 6)
        self.draw_px(sprite, red_light, 18, 15, 2, 6)

        if self.role == "assault":
            self.draw_px(sprite, metal, 5, 11, 2, 13)
            self.draw_px(sprite, metal, 4, 9, 4, 3)
            self.draw_px(sprite, black, 24, 17, 5, 2)
        elif self.role == "heavy":
            self.draw_px(sprite, black, 5, 17, 22, 5)
            self.draw_px(sprite, metal, 25, 15, 4, 2)
            self.draw_px(sprite, red_dark, 8, 14, 5, 4)
        elif self.role == "plasma":
            self.draw_px(sprite, black, 6, 17, 20, 3)
            self.draw_px(sprite, plasma, 19, 16, 5, 2)
            self.draw_px(sprite, plasma, 22, 14, 2, 6)
        else:
            self.draw_px(sprite, black, 7, 17, 18, 3)
            self.draw_px(sprite, metal, 23, 16, 3, 2)

        if self.role == "heavy":
            self.draw_px(sprite, gold, 14, 3, 5, 2)

        self.blit_pixel_sprite(screen, sprite, center, include_shadow=include_shadow)

    def draw_ork_sprite(self, screen, center, include_shadow=True):
        # Простой спрайт орка из прямоугольников.
        skin = (78, 170, 74)
        skin_dark = (32, 82, 38)
        blue = (48, 66, 178)
        blue_dark = (22, 34, 92)
        black = (26, 25, 22)
        metal = (150, 150, 135)
        tusk = (236, 222, 178)
        red = (210, 58, 44)
        yellow = (236, 190, 70)

        sprite = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.draw_px(sprite, black, 8, 27, 16, 2)
        self.draw_px(sprite, blue_dark, 10, 20, 5, 7)
        self.draw_px(sprite, blue_dark, 18, 20, 5, 7)
        self.draw_px(sprite, blue, 10, 15, 13, 8)
        self.draw_px(sprite, blue_dark, 8, 16, 4, 5)
        self.draw_px(sprite, blue_dark, 22, 16, 4, 5)
        self.draw_px(sprite, skin_dark, 8, 8, 16, 8)
        self.draw_px(sprite, skin, 10, 6, 12, 9)
        self.draw_px(sprite, skin_dark, 5, 9, 5, 4)
        self.draw_px(sprite, skin_dark, 22, 9, 5, 4)
        self.draw_px(sprite, black, 12, 9, 2, 2)
        self.draw_px(sprite, black, 18, 9, 2, 2)
        self.draw_px(sprite, tusk, 12, 14, 3, 3)
        self.draw_px(sprite, tusk, 18, 14, 3, 3)

        if self.role == "rokkit":
            self.draw_px(sprite, black, 4, 17, 18, 4)
            self.draw_px(sprite, red, 2, 16, 4, 6)
            self.draw_px(sprite, yellow, 1, 18, 2, 2)
        elif self.role == "nob":
            self.draw_px(sprite, metal, 5, 12, 3, 14)
            self.draw_px(sprite, metal, 3, 10, 7, 4)
            self.draw_px(sprite, blue_dark, 21, 14, 6, 5)
        elif self.role == "boyz":
            self.draw_px(sprite, metal, 4, 10, 2, 14)
            self.draw_px(sprite, metal, 3, 9, 5, 3)
            self.draw_px(sprite, black, 22, 17, 7, 3)
        else:
            self.draw_px(sprite, black, 4, 17, 20, 3)
            self.draw_px(sprite, metal, 23, 16, 4, 2)

        self.blit_pixel_sprite(screen, sprite, center, include_shadow=include_shadow)

    def draw_px(self, sprite, color, x, y, width, height):
        pygame.draw.rect(sprite, color, (x, y, width, height))

    def blit_pixel_sprite(self, screen, sprite, center, include_shadow=True):
        # Увеличиваем маленький спрайт до нужного размера.
        scaled = pygame.transform.scale(sprite, (sprite_size, sprite_size))
        rect = scaled.get_rect(center=(center[0], center[1] - 5))

        if include_shadow:
            shadow = pygame.Surface((46, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
            screen.blit(shadow, (center[0] - 23, center[1] + 18))

        screen.blit(scaled, rect)

    def draw_role_badge(self, screen, center, badge_font):
        cx, cy = center
        if self.role in role_badges:
            badge = role_badges[self.role]
        else:
            badge = self.role[:1].upper()

        if self.faction == "marines":
            badge_color = (255, 220, 100)
        else:
            badge_color = (125, 255, 135)

        rect = pygame.Rect(cx + 10, cy - 24, 18, 16)

        pygame.draw.rect(screen, (28, 29, 28), rect, border_radius=3)
        pygame.draw.rect(screen, badge_color, rect, 1, border_radius=3)

        text = badge_font.render(badge, True, badge_color)
        screen.blit(
            text,
            (
                rect.centerx - text.get_width() // 2,
                rect.centery - text.get_height() // 2,
            ),
        )

    def draw_model_pips(self, screen, center):
        # Точки снизу показывают, сколько моделей осталось.
        cx, cy = center
        max_pips = self.models

        if max_pips > 5:
            max_pips = 5

        start_x = cx - (max_pips - 1) * 4

        for index in range(max_pips):
            pygame.draw.circle(
                screen,
                (235, 235, 225),
                (start_x + index * 8, cy + 25),
                2,
            )
