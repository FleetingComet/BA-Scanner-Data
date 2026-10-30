from pathlib import Path


def _locate_root() -> Path:
    path = Path(__file__).resolve()
    while not (path / "main.py").exists():
        if path.parent == path:
            raise RuntimeError("Could not locate project root.")
        path = path.parent
    return path


PROJECT_ROOT = _locate_root()