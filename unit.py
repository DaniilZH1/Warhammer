import pygame

from settings import *
from weapon import bolter

class Unit:

    def __init__(self, x, y, team):

        self.x = x
        self.y = y
        self.team = team
        self.models = 5
        self.hp_per_model = 2
        self.hp_per_model = 2
        self.models = 5

        self.hp = (
            self.models
            * self.hp_per_model
        )

        # Warhammer stats
        self.ballistic_skill = 3
        self.toughness = 4
        self.armor_save = 3
        self.move_range = 2
        self.weapon = bolter

        self.has_acted = False

        self.max_ap = 2
        self.ap = 2

    def draw(
        self,
        screen,
        font,
        selected=False,
        hovered=False
    ):

        color = RED if self.team == 1 else BLUE

        center = (
            self.x * CELL_SIZE + CELL_SIZE // 2,
            self.y * CELL_SIZE + CELL_SIZE // 2
        )
        # HOVER TARGET
        if hovered:

            pygame.draw.circle(
                screen,
                (255, 255, 0),
                center,
                CELL_SIZE // 2,
                4
            )

         # SELECTED UNIT
        if selected:

            pygame.draw.circle(
                screen,
                GREEN,
                center,
                CELL_SIZE // 2,
                4
            )        

        pygame.draw.circle(
            screen,
            color,
            (
                self.x * CELL_SIZE + CELL_SIZE // 2,
                self.y * CELL_SIZE + CELL_SIZE // 2
            ),
            CELL_SIZE // 3
        )

        hp_text = font.render(str(self.hp), True, WHITE)

        screen.blit(
            hp_text,
            (
                self.x * CELL_SIZE + 10,
                self.y * CELL_SIZE + 10
            )
        )