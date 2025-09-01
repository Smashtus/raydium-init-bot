from __future__ import annotations

from pathlib import Path
from typing import Any

try:  # optional dependency
    import orjson as jsonlib  # type: ignore
except Exception:  # pragma: no cover
    import json as jsonlib  # type: ignore

from src.models.plan import Plan


def read_json(path: Path) -> Any:
    data = path.read_bytes()
    if hasattr(jsonlib, "loads"):
        try:
            return jsonlib.loads(data)
        except TypeError:
            return jsonlib.loads(data.decode("utf-8"))
    import json as stdjson
    return stdjson.loads(data.decode("utf-8"))


def load_plan(path: Path) -> Plan:
    raw = read_json(path)
    return Plan.from_dict(raw)


def write_json(path: Path, obj: Any) -> None:
    if hasattr(jsonlib, "dumps"):
        try:
            path.write_bytes(jsonlib.dumps(obj, option=getattr(jsonlib, 'OPT_INDENT_2', 0)))
            return
        except TypeError:
            pass
    import json as stdjson
    path.write_text(stdjson.dumps(obj, indent=2))
