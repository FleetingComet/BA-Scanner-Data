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


def fetch_and_process(data_type: str, url: str, output_file: str) -> int:
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


def main():
    parser = argparse.ArgumentParser(description="Process SchaleDB data")
    parser.add_argument(
        "--type",
        choices=list(DATA_CONFIGS.keys()),
        help="Type of data to process. Leave empty to process all default types.",
    )
    parser.add_argument("--url", help="Override fetch URL.")
    parser.add_argument("--output", help="Override output JSON filepath.")
    args = parser.parse_args()

    if args.type:
        config = DATA_CONFIGS[args.type]
        url = args.url or f"{DEFAULT_BASE_URL}/{config['filename']}"
        output = args.output or config["output"]
        fetch_and_process(args.type, url, output)
        return

    print("Running batch update for all datasets concurrently...")
    with ThreadPoolExecutor(max_workers=len(DATA_CONFIGS)) as executor:
        futures = []
        for d_type, config in DATA_CONFIGS.items():
            url = f"{DEFAULT_BASE_URL}/{config['filename']}"
            futures.append(
                executor.submit(fetch_and_process, d_type, url, config["output"])
            )

        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    main()
