# Seed/subwallet handling (future). Stubs only.

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class SignerInfo:
    public_key: str
    path: str | None = None

def load_seed_from_file(path: str) -> SignerInfo:
    return SignerInfo(public_key=f"SEED_{path}")

def use_ledger() -> SignerInfo:
    return SignerInfo(public_key="SEED_LEDGER", path="m/44'/501'/0'")
