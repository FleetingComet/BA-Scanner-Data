import dataclasses
import json

import requests

from constant import LOCALIZATION_CONFIG, STUDENT_TRANSLATION_FIELDS
from shapes import Student
from utils import _root_path, write_json_if_changed


def filter_localization(data: dict) -> dict:
    """Keep only the fields we need for student translation."""
    if not isinstance(data, dict):
        raise TypeError("Localization payload must be a JSON object")

    return {
        field: data[field]
        for field in STUDENT_TRANSLATION_FIELDS
        if isinstance(data.get(field), dict)
    }


def fetch_localization(url: str, output_file: str) -> bool:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        filtered = filter_localization(response.json())
        if not filtered:
            raise ValueError("No expected localization fields found")
        changed = write_json_if_changed(output_file, filtered)
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"[localization] Error fetching data: {e}")
        return False

    print(f"[localization] {'Updated' if changed else 'Unchanged'} -> {output_file}")
    return True


def load_localization() -> dict:
    path = _root_path(LOCALIZATION_CONFIG["output"])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return filter_localization(data)
    except (OSError, ValueError) as exc:
        print(f"[localization] Not available: {exc}")
        return {}


def translate_student(student: Student, translations: dict) -> Student:
    """Translate student fields using localization data."""
    updates = {}
    for field in ("SquadType", "BulletType", "ArmorType", "School", "Club"):
        mapping = translations.get(field, {})
        if isinstance(mapping, dict):
            original = getattr(student, field)
            updates[field] = mapping.get(original, original)
    return dataclasses.replace(student, **updates)


def translate_data(data: list, data_type: str, translations: dict) -> list:
    """Translate data based on type."""
    if data_type == "student" and translations:
        return [translate_student(item, translations) for item in data]
    return data
