from __future__ import annotations
from typing import Dict, Any, List
from src.models.plan import Plan, Wallet

def run(plan: Plan) -> Dict[str, Any]:
    # NO CHAIN SIDE EFFECTS YET.
    # Step through schedule and emit fake swap receipts with min_out_tokens respected in output.
    results: List[Dict[str, Any]] = []
    idx = 0
    for wid in plan.schedule:
        w = next(w for w in plan.wallets if w.wallet_id == wid)
        if not w.action or w.action.type not in ("SWAP_BUY", "SWAP_BUY_SOL"):
            continue
        idx += 1
        results.append({
            "order": idx,
            "wallet_id": w.wallet_id,
            "role": w.role,
            "in_sol": w.action.effective_base_sol,
            "min_out_tokens": w.action.min_out_tokens,
            "received_tokens": max(w.action.min_out_tokens, 1),  # deterministic
            "slippage_bps": w.action.slippage_bps,
            "atomic": bool(w.action.atomic),
            "tx_sig": f"FAKE_SIG_SWAP_{idx}",
        })
    return {"swaps": results}
