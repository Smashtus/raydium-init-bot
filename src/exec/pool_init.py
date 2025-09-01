from __future__ import annotations
from typing import Dict, Any
from src.core.solana import Rpc
from src.dex import raydium_v4 as r4


async def run(rpc: Rpc, program_id: str, base_mint: str, quote_mint: str, tokens_to_lp: int, lp_creator_kp, cu_limit: int | None, cu_price_micro: int | None, simulate: bool = False) -> Dict[str, Any]:
    # If pool already exists (caller should know addresses), r4 should expose a check; skip if exists.
    # Codex: implement r4.initialize2 builder + account metas; add compute budget; simulate if requested; send+confirm otherwise, return pool/vaults/lp_mint + sig.
    accounts, sig = await r4.initialize2(
        rpc,
        mint_base=base_mint,
        mint_quote=quote_mint,
        tokens_to_lp=tokens_to_lp,
        payer=lp_creator_kp,
        program_id=program_id,
    )
    res = {
        "pool": accounts.pool,
        "vault_base": accounts.vault_base,
        "vault_quote": accounts.vault_quote,
        "lp_mint": accounts.lp_mint,
    }
    if simulate:
        res["simulated"] = True
    else:
        res["tx_sig"] = sig
    return res
