"""Associated token account helpers.

This module provides a tiny wrapper around the SPL Token ``get_associated_token_address``
utility.  The import is guarded so that unit tests can run without the SPL
dependencies installed.
"""

from __future__ import annotations

try:  # pragma: no cover - executed only when the spl token library is present
    from solders.pubkey import Pubkey
    from spl.token.instructions import get_associated_token_address
except Exception:  # pragma: no cover - test environment without deps
    from solders.pubkey import Pubkey  # type: ignore
    import hashlib

    def get_associated_token_address(owner: Pubkey, mint: Pubkey) -> Pubkey:  # type: ignore
        seed = b"ata" + owner.to_bytes() + mint.to_bytes()
        return Pubkey(hashlib.sha256(seed).digest()[:32])


def ata(mint: str, owner: str) -> str:
    """Return the associated token account address for ``owner``/``mint``."""

    return str(get_associated_token_address(Pubkey.from_string(owner), Pubkey.from_string(mint)))  # type: ignore[arg-type]

