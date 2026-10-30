import json
from pathlib import Path
from urllib.parse import quote

import requests

from constant import DATA_CONFIGS, IMAGE_BASE, IMAGES_DIR
from school_icons import get_school_icon
from utils import _root_path


def _read_processed(config_key: str) -> list[dict]:
    path = _root_path(DATA_CONFIGS[config_key]["output"])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = list(data.values())
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise ValueError("Expected list or dictionary of records")
        return data
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"Could not read processed {config_key} data at {path}: {exc}"
        ) from exc


def _field(record: dict, *names: str):
    for name in names:
        value = record.get(name)
        if value is not None and value != "":
            return value
    return None


def _ensure_extension(name: object, extension: str) -> str:
    text = str(name).strip()
    if not text or text in {".", ".."} or "/" in text or "\\" in text or ".." in text:
        raise ValueError(f"Invalid image name: {name!r}")
    return text if text.casefold().endswith(extension.casefold()) else text + extension


def _download_file(
    url: str,
    dest: Path,
    session: requests.Session,
    failures: list[str],
    *,
    optional: bool = False,
) -> bool:
    """Return whether the file exists/downloaded.

    404 is an expected outcome only for an unknown school icon; other errors fail.
    """
    tmp = dest.with_name(dest.name + ".tmp")

    try:
        if dest.is_file() and dest.stat().st_size > 0:
            return True
        dest.parent.mkdir(parents=True, exist_ok=True)
        with session.get(url, timeout=30, stream=True) as response:
            if optional and response.status_code == 404:
                return False
            response.raise_for_status()
            with tmp.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        stream.write(chunk)
        if not tmp.stat().st_size:
            raise ValueError("Empty download")
        tmp.replace(dest)
        return True
    except (requests.RequestException, OSError, ValueError) as exc:
        print(f"[images] Failed {url}: {exc}")
        failures.append(url)
        return False
    finally:
        tmp.unlink(missing_ok=True)


def _collect_icons(data_type: str) -> set[str]:
    return {
        str(icon).strip()
        for row in _read_processed(data_type)
        if (icon := _field(row, "icon", "Icon"))
    }


def _collect_student_assets() -> tuple[set[str], set[str]]:
    ids: set[str] = set()
    schools: set[str] = set()

    for row in _read_processed("student"):
        sid = _field(row, "id", "Id")
        if sid is None:
            continue
        sid = str(sid)
        ids.add(sid)
        school_icon = get_school_icon(_field(row, "School", "school"), sid)
        if school_icon:
            schools.add(school_icon)

    return ids, schools


def download_images(data_type: str | None = None) -> bool:
    if data_type is not None and data_type not in {
        "item",
        "equipment",
        "student",
        "currency",
    }:
        raise ValueError(f"Unknown data type: {data_type}")
    failures: list[str] = []

    try:
        targets = []
        for kind in ("item", "equipment"):
            if data_type is None or data_type == kind:
                for icon in sorted(_collect_icons(kind)):
                    name = _ensure_extension(icon, ".webp")
                    targets.append((f"{kind}/icon", name))
        if data_type is None or data_type == "student":
            ids, schools = _collect_student_assets()
            targets.extend(
                ("student/collection", _ensure_extension(sid, ".webp"))
                for sid in sorted(ids)
            )
            targets.extend(
                ("schoolicon", _ensure_extension(school, ".png"))
                for school in sorted(schools)
            )
    except (ValueError, RuntimeError) as exc:
        print(f"[images] Cannot collect assets: {exc}")
        return False

    with requests.Session() as session:
        session.headers.update(
            {"User-Agent": "BA-Scanner-Data-SchaleDB-Downloader/1.0"}
        )
        for folder, name in targets:
            url = f"{IMAGE_BASE}{folder}/{quote(name)}"
            if folder != "schoolicon":
                _download_file(url, IMAGES_DIR / folder / name, session, failures)
                continue
            # Discover school assets from current students.json rather than a static list.
            # An unknown school is NOT immediately mapped to ETC: try its own icon first.
            exists = _download_file(
                url, IMAGES_DIR / folder / name, session, failures, optional=True
            )
            if not exists and url not in failures:
                print(f"[images] No icon for {name}; using ETC fallback")
                fallback = "ETC.png"
                _download_file(
                    f"{IMAGE_BASE}schoolicon/{fallback}",
                    IMAGES_DIR / "schoolicon" / fallback,
                    session,
                    failures,
                )

    if failures:
        print(f"[images] {len(failures)} download(s) failed.")
        return False

    print("[images] Image assets are up to date.")
    return True
