"""Raydium v4 pool initialisation."""

from __future__ import annotations

from typing import Any, Dict

from src.core.solana import Rpc
from src.dex import raydium_v4 as r4


async def run(
    rpc: Rpc,
    program_id: str,
    base_mint: str,
    quote_mint: str,
    tokens_to_lp: int,
    lp_creator_kp,
) -> Dict[str, Any]:
    """Initialise a Raydium CPMM pool using ``initialize2``.

    The heavy lifting is delegated to :mod:`src.dex.raydium_v4` which in this
    repository provides placeholder implementations.  The function returns a
    dictionary compatible with the rest of the orchestration layer.
    """

    accounts, sig = await r4.initialize2(
        rpc,
        mint_base=base_mint,
        mint_quote=quote_mint,
        tokens_to_lp=tokens_to_lp,
        payer=lp_creator_kp,
        program_id=program_id,
    )
    return {
        "pool": accounts.pool,
        "vault_base": accounts.vault_base,
        "vault_quote": accounts.vault_quote,
        "lp_mint": accounts.lp_mint,
        "tx_sig": sig,
    }

