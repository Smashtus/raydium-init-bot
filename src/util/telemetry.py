from __future__ import annotations
from pathlib import Path
import orjson, time


class Telemetry:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: dict) -> None:
        event = {**event, "ts_ms": int(time.time()*1000)}
        with self.path.open("ab") as f:
            f.write(orjson.dumps(event))
            f.write(b"\n")
