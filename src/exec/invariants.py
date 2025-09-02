from __future__ import annotations
from src.models.plan import Plan

def assert_plan_invariants(plan: Plan) -> None:
    # Plan.validate() already enforces invariants. Keep a separate hook for runtime checks.
    plan.validate()

def assert_runtime_bounds(plan: Plan) -> None:
    # token decimals 0..9 (SPL supports up to 9)
    if not (0 <= plan.token.decimals <= 9):
        raise ValueError("token.decimals must be between 0 and 9")
    # positive LP tokens
    if plan.token.lp_tokens <= 0:
        raise ValueError("token.lp_tokens must be > 0")
    # slippage bounds and effective_base_sol non-negative
    for w in plan.wallets:
        a = w.action
        if not a:
            continue
        if a.slippage_bps < 0 or a.slippage_bps > 5000:
            raise ValueError(f"slippage_bps out of bounds in wallet {w.wallet_id}")
        if a.effective_base_sol < 0:
            raise ValueError(f"effective_base_sol must be >= 0 in wallet {w.wallet_id}")
