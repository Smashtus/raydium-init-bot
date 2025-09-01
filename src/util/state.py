from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any
import json
from time import time

RECEIPT_SCHEMA_VERSION = "1.0.0"


@dataclass
class StepReceipt:
    step: str
    ok: bool
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    schema_version: str = RECEIPT_SCHEMA_VERSION
    created_ms: int = int(time() * 1000)
    plan_hash: str | None = None


class State:
    def __init__(self, out_dir: Path):
        self.dir = out_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.receipts_dir = self.dir / "receipts"
        self.receipts_dir.mkdir(exist_ok=True)
        self.chk = self.dir / "checkpoints.json"
        self.artifacts_path = self.dir / "artifacts.json"
        if self.chk.exists():
            self.checkpoints = json.loads(self.chk.read_text())
        else:
            self.checkpoints = {"done": []}
        if self.artifacts_path.exists():
            self.artifacts = json.loads(self.artifacts_path.read_text())
        else:
            self.artifacts = {}

    def done(self, step: str) -> bool:
        return step in self.checkpoints.get("done", [])

    def mark(self, step: str, receipt: StepReceipt) -> None:
        self.checkpoints.setdefault("done", []).append(step)
        (self.receipts_dir / f"{step}.json").write_text(
            json.dumps(asdict(receipt), indent=2)
        )
        self.chk.write_text(json.dumps(self.checkpoints, indent=2))

    def merge_artifacts(self, patch: Dict[str, Any]) -> None:
        self.artifacts.update(patch or {})
        self.artifacts_path.write_text(json.dumps(self.artifacts, indent=2))

    def load_receipt(self, step: str) -> Dict[str, Any] | None:
        p = self.receipts_dir / f"{step}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text())
