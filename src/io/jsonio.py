from __future__ import annotations
from pathlib import Path
import orjson
from typing import Any, Dict
from src.models.plan import Plan

def read_json(path: Path) -> Dict[str, Any]:
    return orjson.loads(path.read_bytes())

def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orjson.dumps(obj, option=orjson.OPT_INDENT_2))

def load_plan(path: Path) -> Plan:
    raw = read_json(path)
    return Plan.from_dict(raw)
