import pygame

from settings import *
from weapon import bolter, plasma_gun, shoota


class Unit:
    def __init__(self, x, y, team, faction):
        self.x = x
        self.y = y
        self.team = team
        self.faction = faction

        if faction == "marines":
            self.models = 5
            self.hp_per_model = 2
            self.max_ap = 3
            self.ballistic_skill = 3
            self.toughness = 4
            self.armor_save = 3
            self.melee_attacks = 2
            self.melee_skill = 3
            if x == 1 and y == 1:
                self.weapon = plasma_gun
            else:
                self.weapon = bolter
                
        elif faction == "orks":
            self.models = 10
            self.hp_per_model = 1
            self.max_ap = 2
            self.ballistic_skill = 5
            self.toughness = 5
            self.armor_save = 5
            self.melee_attacks = 4
            self.melee_skill = 4
            self.weapon = shoota
        else:
            raise ValueError(f"Unknown faction: {faction}")

        self.hp = self.models * self.hp_per_model
        self.move_range = 2

        self.has_acted = False
        self.acted_phases = set()
        self.has_charged = False
        self.broken = False
        self.melee_flash = 0

        self.ap = self.max_ap

    def draw(
        self,
        screen,
        font,
        selected=False,
        hovered=False,
        engaged=False,
    ):
        color = RED if self.team == 1 else BLUE

        center = (
            self.x * CELL_SIZE + CELL_SIZE // 2,
            self.y * CELL_SIZE + CELL_SIZE // 2,
        )

        if hovered:
            pygame.draw.circle(
                screen,
                (255, 255, 0),
                center,
                CELL_SIZE // 2,
                4,
            )

        if selected:
            pygame.draw.circle(
                screen,
                GREEN,
                center,
                CELL_SIZE // 2,
                4,
            )

        if engaged:
            pygame.draw.circle(
                screen,
                (255, 120, 0),
                center,
                CELL_SIZE // 2 - 8,
                3,
            )

        if self.melee_flash > 0:
            pygame.draw.circle(
                screen,
                (255, 0, 0),
                center,
                CELL_SIZE // 2,
            )

            self.melee_flash -= 1

        pygame.draw.circle(
            screen,
            color,
            center,
            CELL_SIZE // 3,
        )

        if self.broken:
            pygame.draw.circle(
                screen,
                (255, 0, 255),
                center,
                CELL_SIZE // 3 + 6,
                3,
            )

        hp_text = font.render(str(self.hp), True, WHITE)
        screen.blit(
            hp_text,
            (
                self.x * CELL_SIZE + 10,
                self.y * CELL_SIZE + 10,
            ),
        )
