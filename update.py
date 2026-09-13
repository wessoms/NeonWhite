import copy
import csv
import json
import re
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from typing import Any
from urllib.request import urlopen


SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1CCShf6x4Nd2sQnsBnk788xu3AIUrVkdqzaeORB5UueQ/export?format=csv&gid=1606677618"
)


def load_data() -> tuple[list[str], dict[str, Any]]:
    with TemporaryDirectory() as temporary_directory:
        csv_path = Path(temporary_directory) / "sheet.csv"

        with urlopen(SHEET_URL) as response, csv_path.open("wb") as output_file:
            copyfileobj(response, output_file)

        with csv_path.open("r", encoding="utf-8", newline="") as input_file:
            sheet_values = [row[9] for row in list(csv.reader(input_file))[2:]]

    world_record_path = Path(__file__).resolve().with_name("WorldRecord.json")
    with world_record_path.open("r", encoding="utf-8") as input_file:
        world_record = json.load(input_file)

    return sheet_values, world_record


def time_to_microseconds(time_value: str) -> int:
    match = re.fullmatch(r"(?:(\d+):)?(\d+)(?:\.(\d+))?", time_value.strip())
    if match is None:
        raise ValueError(f"Invalid time value: {time_value!r}")

    minutes, seconds, fractional_seconds = match.groups()
    if int(seconds) >= 60 and minutes is not None:
        raise ValueError(f"Invalid time value: {time_value!r}")

    milliseconds = (fractional_seconds or "").ljust(3, "0")[:3]
    return ((int(minutes or 0) * 60 + int(seconds)) * 1_000_000
        + int(milliseconds) * 1_000
        + 999)


def update_world_record(sheet_values: list[str], world_record: dict[str, Any]) -> bool:
    records = [
        level_record for level_name, level_record in world_record.items()
        if level_name != "_metadata"
    ]

    if len(sheet_values) != len(records):
        raise ValueError(
            f"Expected {len(records)} sheet values, got {len(sheet_values)}"
        )

    original_snapshot = copy.deepcopy(world_record)

    for sheet_value, level_record in zip(sheet_values, records):
        level_record[:] = [time_to_microseconds(sheet_value)]

    if world_record == original_snapshot:
        return False

    world_record_path = Path(__file__).resolve().with_name("WorldRecord.json")
    with world_record_path.open("w", encoding="utf-8") as output_file:
        json.dump(world_record, output_file, indent=4)
        output_file.write("\n")

    return True


if __name__ == "__main__":
    sheet_values, world_record = load_data()
    changed = update_world_record(sheet_values, world_record)
    if changed:
        print(f"Updated {len(world_record)} world record entries")
    else:
        print("No changes detected")