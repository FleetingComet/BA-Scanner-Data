import os

from paths import PROJECT_ROOT

IMAGES_DIR = PROJECT_ROOT / "images"
DEFAULT_BASE_URL = os.getenv("SCHALEDB_BASE_URL", "https://schaledb.com").rstrip("/")
DEFAULT_DATA_BASE = os.getenv(
    "SCHALEDB_DATA_BASE_URL", f"{DEFAULT_BASE_URL}/data/en"
).rstrip("/")
IMAGE_BASE = f"{DEFAULT_BASE_URL}/images/"

DATA_CONFIGS = {
    "item": {
        "filename": "items.min.json",
        "output": "data/items.json",
    },
    "student": {
        "filename": "students.min.json",
        "output": "data/students.json",
    },
    "equipment": {
        "filename": "equipment.min.json",
        "output": "data/equipment.json",
    },
    "currency": {
        "filename": "currency.min.json",
        "output": "data/currency.json",
    },
}

LOCALIZATION_CONFIG = {
    "filename": "localization.min.json",
    "output": "data/localization.json",
}

STUDENT_TRANSLATION_FIELDS = {
    "SquadType",
    "BulletType",
    "ArmorType",
    "TacticRole",
    "School",
    "Club",
}


SCHOOL_ICON_ALIASES = {
    "etc.": "ETC",
    "sakugawa": "ETC",
    # "tokiwadai": "ETC",
    "redwinter": "RedWinter",
    "wildhunt": "WildHunt",  # Filename has an internal capital H.
}
