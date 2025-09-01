import os
import pytest


if not os.environ.get("LIVE_TEST"):
    pytest.skip("LIVE_TEST not set", allow_module_level=True)

# The heavy Solana stack is imported lazily so that this file is skipped on CI
# without requiring the dependencies to be installed.
from pathlib import Path

from src.io.jsonio import load_plan
from src.exec import orchestrator
from src.exec.orchestrator import RunConfig
from src.core.solana import Rpc, RpcConfig
from solders.keypair import Keypair


@pytest.mark.asyncio
async def test_live_smoke_devnet(tmp_path):
    rpc_url = os.environ["DEVNET_RPC"]
    plan = load_plan(Path("plans/sample_plan.json"))
    rpc = Rpc(RpcConfig(url=rpc_url))
    seed = Keypair()

    # Execute the first three steps only: funding -> mint -> metadata
    cfg = RunConfig(out_dir=tmp_path, resume=False, only="funding")
    orchestrator.execute(plan, cfg, rpc=rpc, seed_kp=seed)

    cfg = RunConfig(out_dir=tmp_path, resume=True, only="mint")
    orchestrator.execute(plan, cfg, rpc=rpc, seed_kp=seed)

    cfg = RunConfig(out_dir=tmp_path, resume=True, only="metadata")
    orchestrator.execute(plan, cfg, rpc=rpc, seed_kp=seed)

    rec = tmp_path / "receipts"
    assert (rec / "funding.json").exists()
    assert (rec / "mint.json").exists()
    assert (rec / "metadata.json").exists()

