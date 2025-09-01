from __future__ import annotations
from typing import Dict, Any
from src.models.plan import Plan


def run(plan: Plan, mint_addr: str) -> Dict[str, Any]:
    pool_id = f"POOL_{plan.plan_id}"
    vault_base = f"VAULT_BASE_{pool_id}"
    vault_quote = f"VAULT_QUOTE_{pool_id}"
    return {
        "pool": pool_id,
        "vault_base": vault_base,
        "vault_quote": vault_quote,
        "lp_mint": f"LP_{pool_id}",
        "tx_sig": f"FAKE_SIG_POOL_{pool_id}",
        "tokens_to_lp": plan.token.lp_tokens,
    }
