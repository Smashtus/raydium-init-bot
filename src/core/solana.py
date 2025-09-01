# RPC client & transaction helpers (future). Kept as stubs for now.

from __future__ import annotations

class Rpc:
    def __init__(self, url: str | None):
        self.url = url or ""

    def simulate(self, payload: dict) -> dict:
        return {"ok": True, "payload": payload}
