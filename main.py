import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from constant import (
    DATA_CONFIGS,
    DEFAULT_DATA_BASE,
    LOCALIZATION_CONFIG,
    STUDENT_TRANSLATION_FIELDS,
)
from image_download import download_images
from localization import fetch_localization, load_localization, translate_data
from parsers import (
    parse_currency,
    parse_equipment,
    parse_item,
    parse_student,
    should_include_item,
)
from utils import write_json_if_changed

PARSERS = {
    "item": parse_item,
    "student": parse_student,
    "equipment": parse_equipment,
    "currency": parse_currency,
}


def process_json(data: dict | list, data_type: str) -> list:
    if not isinstance(data, (dict, list)):
        raise TypeError(f"Expected JSON object or array for {data_type}")

    items_iterator = data.values() if isinstance(data, dict) else data
    processed = []

    for item in items_iterator:
        try:
            if not isinstance(item, dict):
                raise TypeError("Entry must be a JSON object")

            if data_type == "item" and not should_include_item(item):
                continue

            processed.append(PARSERS[data_type](item))
        except (KeyError, ValueError, TypeError) as exc:
            print(f"[{data_type}] Skipping entry: {exc}")

    if not processed:
        raise ValueError(f"No valid {data_type} entries; existing output preserved")
    return processed


def fetch_and_process(
    data_type: str, url: str, output_file: str, translations: dict | None = None
) -> bool:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        processed = process_json(response.json(), data_type)
        if translations:
            processed = translate_data(processed, data_type, translations)
        changed = write_json_if_changed(output_file, processed)
    except (requests.RequestException, ValueError, OSError) as exc:
        print(f"[{data_type}] Failed: {exc}")
        return False
    print(
        f"[{data_type}] {len(processed)} entries -> {output_file}"
        f"{' (unchanged)' if not changed else ''}"
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Process SchaleDB data")
    parser.add_argument(
        "-t",
        "--type",
        choices=list(DATA_CONFIGS.keys()),
        help="Only process one dataset, Type of data to process. Leave empty to process all default types.",
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
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip SchaleDB image asset downloads.",
    )
    args = parser.parse_args()

    if args.update_localization:
        url = f"{DEFAULT_DATA_BASE}/{LOCALIZATION_CONFIG['filename']}"
        translations = fetch_localization(url, LOCALIZATION_CONFIG["output"])

    translations = {} if args.no_translate else load_localization()

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
        output = args.output or config["output"]
        url = args.url or f"{DEFAULT_DATA_BASE}/{config['filename']}"
        if not fetch_and_process(args.type, url, output, translations):
            return 1
        # With a custom output path, the image downloader cannot know where to read it.
        if not args.skip_images and not args.output and not download_images(args.type):
            return 1
        return 0

    print("Running batch update for all datasets concurrently...")
    with ThreadPoolExecutor(max_workers=len(DATA_CONFIGS)) as executor:
        tasks = {
            executor.submit(
                fetch_and_process,
                kind,
                f"{DEFAULT_DATA_BASE}/{config['filename']}",
                config["output"],
                translations,
            ): kind
            for kind, config in DATA_CONFIGS.items()
        }

        results = {tasks[future]: future.result() for future in as_completed(tasks)}

    if not all(results.values()):
        print("[main] One or more datasets failed; skipping image downloads")
        return 1

    if not args.skip_images and not download_images():
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
