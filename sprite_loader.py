from pathlib import Path

import pygame

from settings import sprite_size

# Если PNG-спрайта нет, игра просто нарисует запасной спрайт.
sprite_dir = Path(__file__).with_name("assets") / "sprites"
sprite_cache = {}


def sprite_path(faction, role):
    return sprite_dir / f"{faction}_{role}.png"


def load_unit_sprite(faction, role):
    # Запоминаем результат, чтобы не грузить один файл много раз.
    key = (faction, role)

    if key in sprite_cache:
        return sprite_cache[key]

    path = sprite_path(faction, role)

    if not path.exists():
        sprite_cache[key] = None
        return None

    try:
        sprite = pygame.image.load(str(path)).convert_alpha()
    except pygame.error:
        sprite_cache[key] = None
        return None

    sprite_cache[key] = pygame.transform.scale(sprite, (sprite_size, sprite_size))
    return sprite_cache[key]


def clear_sprite_cache():
    sprite_cache.clear()
