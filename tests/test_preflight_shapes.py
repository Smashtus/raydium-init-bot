import asyncio
from pathlib import Path

from src.io.jsonio import load_plan
from src.util.config import load_config
from src.util import preflight


class DummyRpc:
    async def simulate(self, tx, *signers):
        return {"err": None}

    async def account_exists(self, pubkey):
        return True


def test_preflight_shapes():
    plan_path = Path("plans/downstream_plan_mainnet-beta_10000000mint_16.00pctLP_1.0SOL_99pct_3buys.json")
    plan = load_plan(plan_path)
    cfg = load_config(Path("configs/defaults.yaml"))
    rpc = DummyRpc()
    res = asyncio.run(preflight.preflight(rpc, plan_path, cfg, plan))
    assert res["simulate_metadata_ok"]
    assert res["simulate_init_ok"]
    assert res["program_checks"]
