"""Execute SOL→token swaps via Raydium."""

from __future__ import annotations

from typing import Any, Dict, List

from src.models.plan import Plan
from src.core.solana import Rpc
from src.dex import raydium_v4 as r4


async def run(
    rpc: Rpc,
    plan: Plan,
    wallet_map: Dict[str, Any],
    base_mint: str,
    quote_mint: str,
) -> Dict[str, Any]:
    """Execute the swap schedule defined in ``plan``."""

    results: List[Dict[str, Any]] = []
    order = 0
    for wid in plan.schedule:
        w = next(w for w in plan.wallets if w.wallet_id == wid)
        if not w.action or w.action.type not in ("SWAP_BUY", "SWAP_BUY_SOL"):
            continue
        order += 1
        kp = wallet_map[wid]["kp"]
        sig, received = await r4.swap_exact_in_SOL_to_base(
            rpc,
            kp,
            in_lamports=int(w.action.effective_base_sol * 1_000_000_000),
            min_out=w.action.min_out_tokens,
            slippage_bps=w.action.slippage_bps,
            base_mint=base_mint,
            quote_mint=quote_mint,
        )
        results.append(
            {
                "order": order,
                "wallet_id": wid,
                "sig": sig,
                "received_tokens": received,
            }
        )
    return {"swaps": results}

