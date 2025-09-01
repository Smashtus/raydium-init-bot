from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from solders.keypair import Keypair
from pathlib import Path
import json, os, base64
from cryptography.fernet import Fernet


@dataclass
class SignerInfo:
    kp: Keypair


def _fernet() -> Fernet:
    pw = os.environ.get("LAUNCHER_WALLET_PASS", "")
    if not pw:
        raise RuntimeError("LAUNCHER_WALLET_PASS is required")
    key = base64.urlsafe_b64encode(pw.encode().ljust(32, b"\0")[:32])
    return Fernet(key)


def load_seed_from_file(path: str) -> SignerInfo:
    arr = json.loads(Path(path).read_text())
    return SignerInfo(kp=Keypair.from_bytes(bytes(arr)))


def gen_subwallets(ids: List[str]) -> Dict[str, Keypair]:
    return {wid: Keypair() for wid in ids}


def save_encrypted(dirpath: Path, name: str, kp: Keypair) -> str:
    dirpath.mkdir(parents=True, exist_ok=True)
    token = _fernet().encrypt(bytes(kp))
    out = dirpath / f"{name}.enc"
    out.write_bytes(token)
    return str(out)


def pubkey_str(kp: Keypair) -> str:
    return str(kp.pubkey())
