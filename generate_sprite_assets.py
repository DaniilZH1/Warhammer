import os

# Скрипт делает простые PNG-спрайты без открытия окна.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from sprite_loader import clear_sprite_cache
from unit import Unit

sprite_size = 64
canvas_size = 96

units = [
    ("marines", "plasma"),
    ("marines", "tactical"),
    ("marines", "assault"),
    ("marines", "heavy"),
    ("orks", "boyz"),
    ("orks", "shoota"),
    ("orks", "nob"),
    ("orks", "rokkit"),
]


def render_unit_sprite(faction, role):
    # Рисуем такого же юнита, как в игре, и сохраняем его в PNG.
    canvas = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)

    if faction == "marines":
        team = 1
    else:
        team = 2

    unit = Unit(0, 0, team, faction, role)
    center = (canvas_size // 2, canvas_size // 2)

    if faction == "marines":
        unit.draw_marine_sprite(canvas, center, include_shadow=False)
    else:
        unit.draw_ork_sprite(canvas, center, include_shadow=False)

    crop = pygame.Rect(
        (canvas_size - sprite_size) // 2,
        (canvas_size - sprite_size) // 2,
        sprite_size,
        sprite_size,
    )

    return canvas.subsurface(crop).copy()


def main():
    # Сохраняем все спрайты в папку assets/sprites.
    pygame.init()
    output_dir = os.path.join(os.path.dirname(__file__), "assets", "sprites")
    os.makedirs(output_dir, exist_ok=True)

    for faction, role in units:
        sprite = render_unit_sprite(faction, role)
        path = os.path.join(output_dir, f"{faction}_{role}.png")
        pygame.image.save(sprite, path)
        print(path)

    clear_sprite_cache()


if __name__ == "__main__":
    main()
