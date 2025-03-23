import json
from dataclasses import asdict, dataclass
from enum import Enum
import requests
from typing import List, Union
import argparse


class Rarity(Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"


@dataclass
class Item:
    id: int
    name: str


@dataclass
class Student:
    id: int
    name: str


@dataclass
class Equipment:
    id: int
    category: str
    rarity: Rarity
    tier: int
    icon: str
    name: str


def dataclass_to_dict(obj) -> dict:
    data = asdict(obj)
    for key, value in data.items():
        if isinstance(value, Enum):
            data[key] = value.value
    return data


def process_json(data: dict, data_type: str) -> List[Union[Item, Student, Equipment]]:
    processed_list = []
    for item in data.values():
        try:
            if data_type == "item":
                obj = Item(
                    id=int(item["Id"]),
                    name=item["Name"],
                )
            elif data_type == "student":
                obj = Student(
                    id=int(item["Id"]),
                    name=item["Name"],
                )
            elif data_type == "equipment":
                obj = Equipment(
                    id=int(item["Id"]),
                    category=item["Category"],
                    rarity=Rarity(item["Rarity"]),
                    tier=int(item["Tier"]),
                    icon=item["Icon"],
                    name=item["Name"],
                )
            else:
                raise ValueError(f"Invalid data type: {data_type}")
            processed_list.append(obj)
        except (KeyError, ValueError) as e:
            print(f"Skipping invalid entry: {e}")
    return processed_list


def save_json(processed_list: List[Union[Item, Student, Equipment]], output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            [dataclass_to_dict(item) for item in processed_list],
            f,
            indent=4,
            ensure_ascii=False,
        )


def main():
    parser = argparse.ArgumentParser(description="Process SchaleDB data from a URL.")
    parser.add_argument(
        "--type",
        required=True,
        choices=["item", "student", "equipment"],
        help="Type of data to process.",
    )
    parser.add_argument("--url", required=True, help="URL to fetch JSON data.")
    parser.add_argument("--output", required=True, help="Output JSON file name.")
    args = parser.parse_args()

    try:
        response = requests.get(args.url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return
    except json.JSONDecodeError:
        print("Invalid JSON received from URL.")
        return

    processed_data = process_json(data, args.type)
    save_json(processed_data, args.output)
    print(f"Processed {len(processed_data)} entries. Saved to {args.output}")


if __name__ == "__main__":
    main()
