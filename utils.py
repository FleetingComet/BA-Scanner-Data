import dataclasses
import json
import os
import tempfile
from enum import Enum
from pathlib import Path

from constant import PROJECT_ROOT


class CustomJSONEncoder(json.JSONEncoder):
    """Fast JSON encoder handling Enums and Dataclasses."""

    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


def _root_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def write_json_if_changed(path: str | Path, data) -> bool:
    path = _root_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    text = json.dumps(
        data,
        cls=CustomJSONEncoder,
        indent=4,
        ensure_ascii=False,
    )

    try:
        if path.read_text(encoding="utf-8") == text:
            return False
    except FileNotFoundError:
        pass

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp_path = Path(temp.name)
            temp.write(text)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
    return True