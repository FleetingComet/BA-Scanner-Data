import argparse
import dataclasses
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from pathlib import Path

import requests

from parsers import parse_equipment, parse_item, parse_student
from shapes import Equipment, Item, Student

PARSERS = {
    "item": parse_item,
    "student": parse_student,
    "equipment": parse_equipment,
}

DEFAULT_BASE_URL = os.getenv("SCHALEDB_BASE_URL", "https://schaledb.com/data/en")

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


class CustomJSONEncoder(json.JSONEncoder):
    """Fast JSON encoder handling Enums and Dataclasses."""

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


def process_json(data: dict | list, data_type: str) -> list[Item | Student | Equipment]:
    parser_fn = PARSERS[data_type]
    processed_list = []

    # Handle both dict-based and list-based JSON payloads
    items_iterator = data.values() if isinstance(data, dict) else data

    for item in items_iterator:
        try:
            processed_list.append(parser_fn(item))
        except (KeyError, ValueError) as e:
            print(f"[{data_type}] Skipping invalid entry: {e}")

    return processed_list


def fetch_and_process(
    data_type: str, url: str, output_file: str, translations: dict | None = None
) -> int:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"[{data_type}] Error fetching data from {url}: {e}")
        return 0
    except json.JSONDecodeError:
        print(f"[{data_type}] Invalid JSON received from {url}.")
        return 0

    processed_data = process_json(raw_data, data_type)
    if translations:
        processed_data = translate_data(processed_data, data_type, translations)

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            processed_data,
            f,
            cls=CustomJSONEncoder,
            indent=4,
            ensure_ascii=False,
        )

    print(f"[{data_type}] Processed {len(processed_data)} entries -> {output_file}")
    return len(processed_data)


def fetch_localization(url: str, output_file: str) -> dict:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"[localization] Error fetching data: {e}")
        return {}

    filtered_data = filter_localization(raw_data)
    if not filtered_data:
        print("[localization] Warning: No matching fields found in localization data")
        return {}

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            filtered_data,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print(
        f"[localization] Updated -> {output_file} (filtered to {len(filtered_data)} fields)"
    )
    return True


def load_localization() -> dict:
    """Load localization data with caching."""
    try:
        with open(LOCALIZATION_CONFIG["output"], "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[localization] Warning: Could not load localization: {e}")
        return {}


def filter_localization(data: dict) -> dict:
    """Keep only the fields we need for student translation."""
    filtered = {}
    for field in STUDENT_TRANSLATION_FIELDS:
        if field in data:
            filtered[field] = data[field]
    return filtered


def translate_student(student: Student, translations: dict) -> Student:
    """Translate student fields using localization data."""
    squad_type_trans = translations.get("SquadType", {})
    bullet_type_trans = translations.get("BulletType", {})
    armor_type_trans = translations.get("ArmorType", {})
    school_trans = translations.get("School", {})
    club_trans = translations.get("Club", {})

    return dataclasses.replace(
        student,
        SquadType=squad_type_trans.get(student.SquadType, student.SquadType),
        BulletType=bullet_type_trans.get(student.BulletType, student.BulletType),
        ArmorType=armor_type_trans.get(student.ArmorType, student.ArmorType),
        School=school_trans.get(student.School, student.School),
        Club=club_trans.get(student.Club, student.Club),
    )


def translate_data(data: list, data_type: str, translations: dict) -> list:
    """Translate data based on type."""
    if data_type == "student" and translations:
        return [translate_student(item, translations) for item in data]
    return data


def main():
    parser = argparse.ArgumentParser(description="Process SchaleDB data")
    parser.add_argument(
        "-t",
        "--type",
        choices=list(DATA_CONFIGS.keys()),
        help="Type of data to process. Leave empty to process all default types.",
    )
    parser.add_argument("-u", "--url", help="Override fetch URL.")
    parser.add_argument("-o", "--output", help="Override output JSON filepath.")
    parser.add_argument(
        "-l",
        "--update-localization",
        action="store_true",
        help="Download and update the local localization file.",
    )
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="Skip translation even if localization file exists.",
    )
    args = parser.parse_args()

    if args.update_localization:
        url = f"{DEFAULT_BASE_URL}/{LOCALIZATION_CONFIG['filename']}"
        translations = fetch_localization(url, LOCALIZATION_CONFIG["output"])

    translations = {}
    if not args.no_translate:
        translations = load_localization()
        if translations:
            available_fields = set(translations.keys())
            missing_fields = STUDENT_TRANSLATION_FIELDS - available_fields
            print(f"[localization] Loaded {len(translations)} fields")
            if missing_fields:
                print(f"[localization] Missing fields: {', '.join(missing_fields)}")
        else:
            print("[localization] No translations available - skipping")

    if args.type:
        config = DATA_CONFIGS[args.type]
        url = args.url or f"{DEFAULT_BASE_URL}/{config['filename']}"
        output = args.output or config["output"]
        fetch_and_process(
            args.type, url, output, translations if not args.no_translate else None
        )
        return

    print("Running batch update for all datasets concurrently...")
    with ThreadPoolExecutor(max_workers=len(DATA_CONFIGS)) as executor:
        futures = []
        for d_type, config in DATA_CONFIGS.items():
            url = f"{DEFAULT_BASE_URL}/{config['filename']}"
            futures.append(
                executor.submit(
                    fetch_and_process,
                    d_type,
                    url,
                    config["output"],
                    translations if not args.no_translate else None,
                )
            )

        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
