import json
from pathlib import Path

# settings.json хранит настройки игрока.
settings_path = Path(__file__).with_name("settings.json")
default_settings = {
    "ai_orks_enabled": False,
    "dice_delay_ms": 80,
}


def load_app_settings():
    # Если файла нет, берем настройки по умолчанию.
    if not settings_path.exists():
        return default_settings.copy()

    try:
        with settings_path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, json.JSONDecodeError):
        return default_settings.copy()

    settings = default_settings.copy()
    settings.update({
        key: loaded[key]
        for key in default_settings
        if key in loaded
    })
    return settings


def save_app_settings(settings):
    # Сохраняем только нужные настройки.
    stored = default_settings.copy()
    stored.update({
        key: settings[key]
        for key in default_settings
        if key in settings
    })

    with settings_path.open("w", encoding="utf-8") as file:
        json.dump(stored, file, indent=2)
