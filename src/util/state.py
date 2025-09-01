from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any
import json

@dataclass
class StepReceipt:
    step: str
    ok: bool
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]

class State:
    def __init__(self, out_dir: Path):
        self.dir = out_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.receipts_dir = self.dir / "receipts"
        self.receipts_dir.mkdir(exist_ok=True)
        self.chk = self.dir / "checkpoints.json"
        if self.chk.exists():
            self.checkpoints = json.loads(self.chk.read_text())
        else:
            self.checkpoints = {"done": []}

    def done(self, step: str) -> bool:
        return step in self.checkpoints.get("done", [])

    def mark(self, step: str, receipt: StepReceipt) -> None:
        self.checkpoints.setdefault("done", []).append(step)
        (self.receipts_dir / f"{step}.json").write_text(
            json.dumps(asdict(receipt), indent=2)
        )
        self.chk.write_text(json.dumps(self.checkpoints, indent=2))
