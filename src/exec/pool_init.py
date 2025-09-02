from __future__ import annotations
from typing import Dict, Any
from solana.transaction import Transaction
from src.core.solana import Rpc
from src.core.tx import with_compute_budget
from src.dex.raydium_v4 import (
    derive_pool_accounts,
    build_initialize2,
)


async def run(
    rpc: Rpc,
    program_id: str,
    base_mint: str,
    quote_mint: str,
    tokens_to_lp: int,
    lp_creator_kp,
    cu_limit: int | None,
    cu_price_micro: int | None,
    simulate: bool = False,
) -> Dict[str, Any]:
    accounts = derive_pool_accounts(base_mint, quote_mint, program_id)
    tx = Transaction()
    with_compute_budget(tx, cu_limit, cu_price_micro)
    for ix in build_initialize2(program_id, base_mint, quote_mint, str(lp_creator_kp.pubkey()), tokens_to_lp):
        tx.add(ix)
    tx.recent_blockhash = await rpc.recent_blockhash()
    res = {
        "pool": accounts.pool,
        "vault_base": accounts.vault_base,
        "vault_quote": accounts.vault_quote,
        "lp_mint": accounts.lp_mint,
    }
    if simulate:
        sim = await rpc.simulate(tx, lp_creator_kp)
        res["simulated"] = True
        if sim.get("logs"):
            res["logs"] = sim["logs"]
    else:
        sig = await rpc.send_and_confirm(tx, lp_creator_kp)
        res["tx_sig"] = sig
    return res
