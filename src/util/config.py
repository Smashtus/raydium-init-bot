from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
import yaml


def load_config(path: Path | None) -> Dict[str, Any]:
    if path is None:
        path = Path("configs/defaults.yaml")
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    return data or {}
