"""Key management utilities.

The real launcher derives a number of ephemeral wallets from an initial seed
and stores them encrypted on disk.  For unit testing we merely need the
interface; the implementation below mirrors the production code but keeps all
heavy operations optional so that importing the module does not require the
Solana stack to be installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import base64
import json
import os


try:  # pragma: no cover - executed only when the solders/crypto deps exist
    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover - fallback used in tests without deps
    Keypair = object  # type: ignore
    Pubkey = object  # type: ignore

    class Fernet:  # minimal stub; methods raise if used
        def __init__(self, _key: bytes) -> None:
            pass

        def encrypt(self, _data: bytes) -> bytes:  # pragma: no cover - never hit
            raise RuntimeError("Fernet operations require cryptography package")


@dataclass
class SignerInfo:
    """Container for a keypair used for signing."""

    kp: Keypair


def _fernet_from_env() -> Fernet:
    """Create a :class:`Fernet` instance using ``LAUNCHER_WALLET_PASS``.

    The password is padded/truncated to 32 bytes and then base64 url-safe
    encoded which matches what ``Fernet`` expects.
    """

    pw = os.environ.get("LAUNCHER_WALLET_PASS", "")
    if not pw:
        raise RuntimeError("LAUNCHER_WALLET_PASS is required to encrypt wallets")
    key = base64.urlsafe_b64encode(pw.encode().ljust(32, b"\0")[:32])
    return Fernet(key)


def load_seed_from_file(path: str) -> SignerInfo:
    """Load a seed keypair from a JSON array of 64 integers."""

    arr = json.loads(Path(path).read_text())
    kp = Keypair.from_bytes(bytes(arr))  # type: ignore[attr-defined]
    return SignerInfo(kp=kp)


def save_encrypted_wallet(dirpath: Path, name: str, kp: Keypair) -> str:
    """Encrypt ``kp`` and store it under ``dirpath/name.enc``."""

    dirpath.mkdir(parents=True, exist_ok=True)
    token = _fernet_from_env().encrypt(bytes(kp))  # type: ignore[call-arg]
    out = dirpath / f"{name}.enc"
    out.write_bytes(token)
    return str(out)


def derive_fresh_wallets(prefix: str, count: int) -> List[Keypair]:
    """Generate ``count`` new random keypairs."""

    return [Keypair() for _ in range(count)]  # type: ignore[call-arg]


def pubkey_str(kp: Keypair) -> str:
    """Convenience helper to turn a keypair into a base58 string."""

    return str(kp.pubkey())  # type: ignore[call-arg]

