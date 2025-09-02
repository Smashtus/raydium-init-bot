from __future__ import annotations

from typing import Dict, Any, List
from solana.transaction import Transaction

from src.models.plan import Plan
from src.core.solana import Rpc
from src.core.tx import with_compute_budget
from src.dex.raydium_v4 import derive_pool_accounts, build_swap_SOL_to_base
from src.core.ata import ata


async def run(
    rpc: Rpc,
    plan: Plan,
    wallet_map: Dict[str, Any],
    base_mint: str,
    quote_mint: str,
    program_id: str,
    cu_limit: int | None,
    cu_price_micro: int | None,
    simulate: bool = False,
    buys_done: Dict[str, bool] | None = None,
) -> Dict[str, Any]:
    """Execute the buy schedule using Raydium swap instructions.

    ``buys_done`` holds a persistent map of wallet IDs that have already
    completed their swap.  This allows the function to be re‑run idempotently on
    resume without duplicating on‑chain state.
    """

    if buys_done is None:
        buys_done = {}
    results: List[Dict[str, Any]] = []
    order = 0
    accounts = derive_pool_accounts(base_mint, quote_mint, program_id)
    for wid in plan.schedule:
        w = next(w for w in plan.wallets if w.wallet_id == wid)
        if not w.action or w.action.type not in ("SWAP_BUY", "SWAP_BUY_SOL"):
            continue
        order += 1
        if buys_done.get(wid):
            results.append({"order": order, "wallet_id": wid, "skipped": True, "reason": "already_swapped"})
            continue
        kp = wallet_map[wid]["kp"]
        tx = Transaction()
        with_compute_budget(tx, cu_limit, cu_price_micro)
        user_pub = wallet_map[wid]["pub"]
        # Derive user source/destination ATAs; builder references these implicitly
        _user_wsol = ata(quote_mint, user_pub)
        _user_base = ata(base_mint, user_pub)
        for ix in build_swap_SOL_to_base(
            program_id,
            accounts,
            user_pub,
            in_lamports=int(w.action.effective_base_sol * 1_000_000_000),
            min_out=w.action.min_out_tokens,
            slippage_bps=w.action.slippage_bps,
        ):
            tx.add(ix)
        tx.recent_blockhash = await rpc.recent_blockhash()
        if simulate:
            await rpc.simulate(tx, kp)
            results.append({"order": order, "wallet_id": wid, "simulated": True})
        else:
            sig = await rpc.send_and_confirm(tx, kp)
            results.append({"order": order, "wallet_id": wid, "sig": sig})
        buys_done[wid] = True
    return {"swaps": results}

