# Тут описаны параметры оружия.
class Weapon:
    def __init__(
        self,
        name,
        attacks,
        strength,
        ap,
        damage,
        weapon_range,
        special_rules=None,
    ):
        self.name = name
        self.attacks = attacks
        self.strength = strength
        self.ap = ap
        self.damage = damage
        self.weapon_range = weapon_range
        self.special_rules = special_rules or []


bolter = Weapon(
    "Bolter",
    attacks=2,
    strength=4,
    ap=-1,
    damage=1,
    weapon_range=4,
    special_rules=[
        "sustained_hits",
        "rapid_fire",
    ],
)

plasma_gun = Weapon(
    "Plasma Gun",
    attacks=1,
    strength=7,
    ap=-3,
    damage=3,
    weapon_range=5,
)

heavy_bolter = Weapon(
    "Heavy Bolter",
    attacks=3,
    strength=5,
    ap=-1,
    damage=2,
    weapon_range=6,
    special_rules=[
        "sustained_hits",
    ],
)

bolt_pistol = Weapon(
    "Bolt Pistol",
    attacks=1,
    strength=4,
    ap=0,
    damage=1,
    weapon_range=2,
)

shoota = Weapon(
    "Shoota",
    attacks=3,
    strength=4,
    ap=0,
    damage=1,
    weapon_range=3,
)

slugga = Weapon(
    "Slugga",
    attacks=1,
    strength=4,
    ap=0,
    damage=1,
    weapon_range=2,
)

rokkit_launcha = Weapon(
    "Rokkit Launcha",
    attacks=1,
    strength=8,
    ap=-2,
    damage=3,
    weapon_range=5,
)
