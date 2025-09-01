from __future__ import annotations
from typing import Dict, Any
from src.models.plan import Plan, Wallet

def run(plan: Plan) -> Dict[str, Any]:
    # NO CHAIN SIDE EFFECTS YET.
    # Pretend we derived subwallets & transferred lamports. Return deterministic placeholders.
    summary = []
    for w in plan.wallets:
        if w.role == "SEED":
            continue
        summary.append({
            "wallet_id": w.wallet_id,
            "role": w.role,
            "funded_lamports": w.funding.total_lamports,
            "tx_sig": f"FAKE_SIG_{w.wallet_id}",
        })
    return {"funded": summary, "seed_wallet": next(w.wallet_id for w in plan.wallets if w.role=="SEED")}
