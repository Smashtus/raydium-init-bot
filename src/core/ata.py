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
    Pubkey = object  # type: ignore

    def get_associated_token_address(*_args, **_kwargs):  # type: ignore
        raise RuntimeError("spl.token library is required for ATA derivation")


def ata(mint: str, owner: str) -> str:
    """Return the associated token account address for ``owner``/``mint``."""

    return str(get_associated_token_address(Pubkey.from_string(owner), Pubkey.from_string(mint)))  # type: ignore[arg-type]

