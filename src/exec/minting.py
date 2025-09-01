from __future__ import annotations
from typing import Dict, Any
from src.models.plan import Plan


def run(plan: Plan) -> Dict[str, Any]:
    # deterministic stand-in for minting
    fake_mint = f"MINT_{plan.plan_id}"
    lp_creator = next(w for w in plan.wallets if w.role == "LP_CREATOR").wallet_id
    lp_creator_ata = f"ATA_{fake_mint}_{lp_creator}"
    return {
        "mint": fake_mint,
        "lp_creator_ata": lp_creator_ata,
        "minted_tokens": plan.token.lp_tokens,
        "tx_sig": f"FAKE_SIG_MINT_{plan.plan_id}",
    }
