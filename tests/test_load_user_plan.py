from pathlib import Path
from src.io.jsonio import load_plan

def test_load_user_plan():
    p = Path("plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json")
    plan = load_plan(p)
    assert plan.token.lp_tokens == int(plan.inputs.T0)
    schedule_ids = set(plan.schedule)
    wallet_ids = {w.wallet_id for w in plan.wallets}
    assert schedule_ids.issubset(wallet_ids)

